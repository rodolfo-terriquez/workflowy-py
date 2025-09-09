from __future__ import annotations

import re
from typing import Any, List, Literal, Optional, Union
from datetime import datetime

import httpx

from . import config
from .errors import AuthError, ClientError, NotFoundError, RateLimitError, ServerError
from .models import (
    CreateNodePayload,
    CreateNodeResponse,
    GetNodeResponse,
    ListNodesResponse,
    Node,
    UpdateNodePayload,
)


class WorkflowyClient:
    def __init__(
        self,
        api_token: Optional[str] = None,
        base_url: str = config.DEFAULT_BASE_URL,
        timeout: float = config.DEFAULT_TIMEOUT,
    ):
        token = config.discover_token(api_token)
        if not token:
            raise AuthError(
                "No API token provided. Pass it to the client, "
                f"set the {config.ENV_TOKEN_NAME} environment variable, "
                f"or create a config file at {config.CONFIG_FILE}."
            )

        self._client = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )

    def _handle_response(self, response: httpx.Response) -> None:
        if response.is_success:
            return

        status_code = response.status_code
        if status_code == 401:
            raise AuthError(response=response)
        if status_code == 404:
            raise NotFoundError(response=response)
        if status_code == 429:
            raise RateLimitError(response=response)
        if 400 <= status_code < 500:
            raise ClientError(response=response)
        if 500 <= status_code < 600:
            raise ServerError(response=response)

        response.raise_for_status()

    def find_node_by_path(self, path: str, parent: Union[str, Node] = "root") -> Node:
        """
        Find a node by its /-separated path.

        Args:
            path: A string path, e.g., "Projects/My Project/Current Task".
            parent: The node to start the search from. Can be a Node object,
                    ID, path, or "root". Defaults to "root".

        Returns:
            The found Node object.

        Raises:
            NotFoundError: If any part of the path does not exist.
        """
        parent_id = self._resolve_target(parent)
        path_parts = [part for part in path.split("/") if part]

        current_node_id = parent_id
        for i, part in enumerate(path_parts):
            children = self.list_nodes(current_node_id)
            found_child = next((c for c in children if c.name == part), None)

            if not found_child:
                partial_path = "/".join(path_parts[: i + 1])
                raise NotFoundError(f"Node not found at path: '{partial_path}'")

            current_node_id = found_child.id

        return self.get_node(current_node_id)

    def _resolve_target(self, target: Union[str, Node]) -> str:
        """Resolves a user-provided target into a definitive node ID."""
        if isinstance(target, Node):
            return target.id

        if not isinstance(target, str):
            raise TypeError("Target must be a Node object or a string.")

        # Is it a UUID-like ID?
        if re.match(r"^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$", target):
            return target
        
        if target == "root":
            return "root"

        # Assume it's a path
        try:
            found_node = self.find_node_by_path(target)
            return found_node.id
        except NotFoundError as e:
            # Re-raise to provide a more helpful message to the user
            raise NotFoundError(
                f"Could not resolve target '{target}'. "
                "It is not a valid ID, and no node was found at that path."
            ) from e

    def get_node(self, target: Union[str, Node]) -> Node:
        """Retrieve a single node by its ID, path, or object."""
        node_id = self._resolve_target(target)
        if node_id == "root":
            # The API does not provide a way to fetch the root node directly.
            # We synthesize a representation of it, which is sufficient for
            # operations that require a parent ID.
            now = int(datetime.now().timestamp())
            return Node(id="root", name="Home", priority=0, createdAt=now, modifiedAt=now)

        response = self._client.get(f"/nodes/{node_id}")
        self._handle_response(response)
        get_response = GetNodeResponse.model_validate(response.json())
        return get_response.node

    def list_nodes(
        self, parent: Union[str, Node] = "root", sort_by_priority: bool = True
    ) -> List[Node]:
        """List child nodes under a given parent."""
        parent_id = self._resolve_target(parent)
        # The API is inconsistent: creating a node uses `parentId="root"`, but
        # listing top-level nodes requires `parent_id="None"` as a string literal.
        effective_parent_id = "None" if parent_id == "root" else parent_id
        response = self._client.get(
            "/nodes", params={"parent_id": effective_parent_id}
        )
        self._handle_response(response)

        list_response = ListNodesResponse.model_validate(response.json())
        nodes = list_response.nodes

        if sort_by_priority:
            nodes.sort(key=lambda n: n.priority)

        return nodes

    def create_node(
        self,
        parent: Union[str, Node],
        name: str,
        position: Optional[Union[Literal["top", "bottom"], int]] = "top",
        note: Optional[str] = None,
    ) -> Node:
        """Create a new node."""
        parent_id = self._resolve_target(parent)
        # For top-level nodes, the API requires `parent_id` to be JSON `null`.
        effective_parent_id: Optional[str] = parent_id
        if parent_id == "root":
            effective_parent_id = None

        payload = CreateNodePayload(
            parent_id=effective_parent_id,
            name=name,
            position=position,
            note=note,
        )

        # We do NOT `exclude_none` here, so `parent_id: None` becomes `parent_id: null`.
        response = self._client.post("/nodes", json=payload.model_dump())
        self._handle_response(response)
        create_response = CreateNodeResponse.model_validate(response.json())
        return self.get_node(create_response.item_id)

    def update_node(
        self,
        target: Union[str, Node],
        name: Optional[str] = None,
        note: Optional[str] = None,
        priority: Optional[int] = None,
        data: Optional[dict[str, Any]] = None,
    ) -> Node:
        """Update an existing node."""
        node_id = self._resolve_target(target)
        payload = UpdateNodePayload(
            name=name,
            note=note,
            priority=priority,
            data=data,
        )

        response = self._client.post(
            f"/nodes/{node_id}",
            json=payload.model_dump(by_alias=True, exclude_none=True),
        )
        self._handle_response(response)
        return self.get_node(node_id)

    def complete_node(self, target: Union[str, Node]) -> Node:
        """
        Complete an existing node.

        Returns:
            The updated node.
        """
        node_id = self._resolve_target(target)
        response = self._client.post(f"/nodes/{node_id}/complete")
        self._handle_response(response)
        return self.get_node(node_id)

    def uncomplete_node(self, target: Union[str, Node]) -> Node:
        """
        Uncomplete an existing node.

        Returns:
            The updated node.
        """
        node_id = self._resolve_target(target)
        response = self._client.post(f"/nodes/{node_id}/uncomplete")
        self._handle_response(response)
        return self.get_node(node_id)

    def delete_node(self, target: Union[str, Node]) -> None:
        """Delete an existing node."""
        node_id = self._resolve_target(target)
        response = self._client.delete(f"/nodes/{node_id}")
        self._handle_response(response)

    # Convenience methods
    def list_children_sorted(self, parent: Union[str, Node] = "root") -> List[Node]:
        """List and sort child nodes by priority."""
        return self.list_nodes(parent, sort_by_priority=True)

    def create_child_top(
        self, parent: Union[str, Node], name: str, note: Optional[str] = None
    ) -> Node:
        """Create a new child node at the top of the list."""
        return self.create_node(parent, name, position="top", note=note)

    def create_child_bottom(
        self, parent: Union[str, Node], name: str, note: Optional[str] = None
    ) -> Node:
        """Create a new child node at the bottom of the list."""
        return self.create_node(parent, name, position="bottom", note=note)
