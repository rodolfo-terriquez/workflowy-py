import os

import pytest
from workflowy_py import WorkflowyClient

# Mark all tests in this file as 'integration'
pytestmark = pytest.mark.skipif(
    not os.getenv("WORKFLOWY_API_TOKEN"),
    reason="WORKFLOWY_API_TOKEN environment variable not set",
)


@pytest.fixture(scope="module")
def client():
    """Module-scoped client for integration tests."""
    return WorkflowyClient()


def test_get_root_node(client: WorkflowyClient):
    """Test that we can retrieve the root node."""
    root = client.get_node("root")
    assert root.id == "root"
    assert isinstance(root.name, str)


def test_list_and_create_and_delete(client: WorkflowyClient):
    """
    Test a full CRUD-like cycle:
    1. List root children.
    2. Create a new node.
    3. Verify it's in the list.
    4. Delete the new node.
    5. Verify it's gone.
    """
    root_id = "root"
    node_name = "[TEST] Integration Test Node"

    # 1. Initial list
    initial_children = client.list_nodes(root_id)
    initial_child_ids = {c.id for c in initial_children}

    # 2. Create node
    new_node = client.create_child_bottom(root_id, node_name)
    assert new_node.name == node_name

    # 3. Verify creation
    children_after_create = client.list_nodes(root_id)
    assert len(children_after_create) == len(initial_children) + 1

    created_node_found = any(n.id == new_node.id for n in children_after_create)
    assert created_node_found, "Newly created node not found in children list"

    # 4. Delete node
    client.delete_node(new_node.id)

    # 5. Verify deletion
    children_after_delete = client.list_nodes(root_id)
    assert len(children_after_delete) == len(initial_children)
    final_child_ids = {c.id for c in children_after_delete}
    assert new_node.id not in final_child_ids
    assert final_child_ids == initial_child_ids
