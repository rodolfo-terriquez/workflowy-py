from unittest import mock

import pytest
import respx
from httpx import Response
from workflowy_py import WorkflowyClient
from workflowy_py.errors import (
    AuthError,
    ClientError,
    NotFoundError,
    RateLimitError,
    ServerError,
)


@pytest.fixture
def client():
    return WorkflowyClient(api_token="test_token")


def test_client_init_no_token():
    """Verify AuthError is raised if no token is discoverable."""
    with pytest.raises(AuthError, match="No API token provided"):
        WorkflowyClient()


@respx.mock
def test_get_node(client: WorkflowyClient):
    """Test retrieving a single node."""
    node_id = "abc-123"
    mock_response = {
        "id": node_id,
        "name": "Test Node",
        "note": "A note.",
        "priority": 0,
        "createdAt": 1672531200,
        "modifiedAt": 1672531200,
        "completedAt": None,
    }
    respx.get(f"https://workflowy.com/api/v1/nodes/{node_id}").mock(
        return_value=Response(200, json=mock_response)
    )

    node = client.get_node(node_id)
    assert node.id == node_id
    assert node.name == "Test Node"
    assert node.note == "A note."


@respx.mock
def test_list_nodes(client: WorkflowyClient):
    """Test listing child nodes."""
    parent_id = "parent-123"
    mock_response = [
        {
            "id": "child-2",
            "name": "Child 2",
            "priority": 2,
            "createdAt": 1,
            "modifiedAt": 1,
        },
        {
            "id": "child-1",
            "name": "Child 1",
            "priority": 1,
            "createdAt": 1,
            "modifiedAt": 1,
        },
    ]
    respx.get(
        "https://workflowy.com/api/v1/nodes", params={"parent_id": parent_id}
    ).mock(return_value=Response(200, json=mock_response))

    # Test with default sorting (by priority)
    nodes = client.list_nodes(parent_id)
    assert len(nodes) == 2
    assert [n.id for n in nodes] == ["child-1", "child-2"]

    # Test without sorting
    nodes_unsorted = client.list_nodes(parent_id, sort_by_priority=False)
    assert len(nodes_unsorted) == 2
    assert [n.id for n in nodes_unsorted] == ["child-2", "child-1"]


@respx.mock
def test_create_node(client: WorkflowyClient):
    """Test creating a new node."""
    parent_id = "parent-123"
    node_name = "New Node"
    mock_request_payload = {"parentId": parent_id, "name": node_name, "position": "top"}
    mock_response = {
        "id": "new-node-id",
        "name": node_name,
        "note": None,
        "priority": 0,
        "createdAt": 1672531201,
        "modifiedAt": 1672531201,
        "completedAt": None,
    }
    respx.post("https://workflowy.com/api/v1/nodes", json=mock_request_payload).mock(
        return_value=Response(200, json=mock_response)
    )

    node = client.create_node(parent_id, node_name)
    assert node.id == "new-node-id"
    assert node.name == node_name


@respx.mock
def test_create_node_with_note_and_position(client: WorkflowyClient):
    """Test creating a new node with a note and specific position."""
    parent_id = "parent-123"
    node_name = "Another Node"
    node_note = "This is a note."
    node_position = 0

    mock_request_payload = {
        "parentId": parent_id,
        "name": node_name,
        "position": node_position,
        "note": node_note,
    }

    mock_response = {
        "id": "another-node-id",
        "name": node_name,
        "note": node_note,
        "priority": 0,
        "createdAt": 1672531202,
        "modifiedAt": 1672531202,
        "completedAt": None,
    }

    respx.post("https://workflowy.com/api/v1/nodes", json=mock_request_payload).mock(
        return_value=Response(200, json=mock_response)
    )

    node = client.create_node(
        parent_id, node_name, position=node_position, note=node_note
    )
    assert node.id == "another-node-id"
    assert node.note == node_note


@respx.mock
def test_update_node(client: WorkflowyClient):
    """Test updating an existing node."""
    node_id = "node-to-update"
    new_name = "Updated Name"
    new_note = "Updated note."

    mock_request_payload = {"name": new_name, "note": new_note}
    mock_response = {
        "id": node_id,
        "name": new_name,
        "note": new_note,
        "priority": 0,
        "createdAt": 1672531200,
        "modifiedAt": 1672531203,
        "completedAt": None,
    }

    respx.post(
        f"https://workflowy.com/api/v1/nodes/{node_id}", json=mock_request_payload
    ).mock(return_value=Response(200, json=mock_response))

    node = client.update_node(node_id, name=new_name, note=new_note)
    assert node.name == new_name
    assert node.note == new_note
    assert node.modified_at == 1672531203


@respx.mock
def test_complete_node_with_response_body(client: WorkflowyClient):
    """Test completing a node when the API returns the updated node."""
    node_id = "node-to-complete"
    mock_response = {
        "id": node_id,
        "name": "Completed Task",
        "note": None,
        "priority": 0,
        "createdAt": 1672531200,
        "modifiedAt": 1672531204,
        "completedAt": 1672531204,
    }
    respx.post(f"https://workflowy.com/api/v1/nodes/{node_id}/complete").mock(
        return_value=Response(200, json=mock_response)
    )

    node = client.complete_node(node_id)
    assert node is not None
    assert node.completed_at is not None


@respx.mock
def test_complete_node_with_empty_response(client: WorkflowyClient):
    """Test completing a node when the API returns an empty response."""
    node_id = "node-to-complete-no-body"
    respx.post(f"https://workflowy.com/api/v1/nodes/{node_id}/complete").mock(
        return_value=Response(204)
    )

    result = client.complete_node(node_id)
    assert result is None


@respx.mock
def test_uncomplete_node(client: WorkflowyClient):
    """Test uncompleting a node."""
    node_id = "node-to-uncomplete"
    mock_response = {
        "id": node_id,
        "name": "Uncompleted Task",
        "note": None,
        "priority": 0,
        "createdAt": 1672531200,
        "modifiedAt": 1672531205,
        "completedAt": None,
    }
    respx.post(f"https://workflowy.com/api/v1/nodes/{node_id}/uncomplete").mock(
        return_value=Response(200, json=mock_response)
    )

    node = client.uncomplete_node(node_id)
    assert node is not None
    assert node.completed_at is None


@respx.mock
def test_delete_node(client: WorkflowyClient):
    """Test deleting a node."""
    node_id = "node-to-delete"
    respx.delete(f"https://workflowy.com/api/v1/nodes/{node_id}").mock(
        return_value=Response(204)
    )

    client.delete_node(node_id)


def test_list_children_sorted(client: WorkflowyClient):
    """Test the list_children_sorted convenience method."""
    with mock.patch.object(client, "list_nodes") as mock_list:
        client.list_children_sorted("parent-id")
        mock_list.assert_called_once_with("parent-id", sort_by_priority=True)


def test_create_child_top(client: WorkflowyClient):
    """Test the create_child_top convenience method."""
    with mock.patch.object(client, "create_node") as mock_create:
        client.create_child_top("parent-id", "name", note="a note")
        mock_create.assert_called_once_with(
            "parent-id", "name", position="top", note="a note"
        )


def test_create_child_bottom(client: WorkflowyClient):
    """Test the create_child_bottom convenience method."""
    with mock.patch.object(client, "create_node") as mock_create:
        client.create_child_bottom("parent-id", "name", note="a note")
        mock_create.assert_called_once_with(
            "parent-id", "name", position="bottom", note="a note"
        )


@respx.mock
@pytest.mark.parametrize(
    "status_code, error",
    [
        (401, AuthError),
        (404, NotFoundError),
        (429, RateLimitError),
        (400, ClientError),
        (500, ServerError),
        (503, ServerError),
    ],
)
def test_error_handling(
    client: WorkflowyClient, status_code: int, error: type[Exception]
):
    """Test that HTTP errors are mapped to the correct exception types."""
    node_id = "error-node"
    url = f"https://workflowy.com/api/v1/nodes/{node_id}"
    respx.get(url).mock(return_value=Response(status_code))

    with pytest.raises(error):
        client.get_node(node_id)
