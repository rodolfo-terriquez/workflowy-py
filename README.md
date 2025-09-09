# workflowy-py

> **Warning: Use at Your Own Risk**
>
> This software is provided "as is", without warranty of any kind. By using this library, you assume full responsibility for any accidental deletion, modification, or corruption of your Workflowy data. It is highly recommended that you create a backup of your data before performing any write operations.

A clean, typed, sync Python client for the [Workflowy API](https://workflowy.com/api/docs/).

## Installation

```bash
pip install workflowy-py
```

## Authentication

The client discovers the API token in the following order:
1.  Directly passed to the client: `WorkflowyClient(api_token="YOUR_TOKEN")`
2.  Environment variable: `WORKFLOWY_API_TOKEN`
3.  Configuration file: `~/.workflowy/config` (a plain text file with your token)

If no token is found, an `AuthError` is raised.

## Targeting Nodes

All client methods that interact with a specific node (like `get_node`, `update_node`, `create_node`, etc.) accept a flexible `target` argument. This can be one of three things:

1.  **Node ID String**: The full, unique ID of a node. This is the most precise way to target a node.
    ```python
    client.get_node("a5ed28fa-c9f6-439a-adcc-762378b295af")
    ```

2.  **Node Path String**: A `/`-separated path representing the node's location. The client will traverse the tree to find it. This is the most convenient way for programmatic access.
    ```python
    client.update_node("Projects/My Project/Tasks", note="An important update.")
    ```

3.  **Node Object**: Any `Node` object that you have already fetched.
    ```python
    project_node = client.find_node_by_path("Projects/My Project")
    # Now you can use the object directly
    tasks = client.list_nodes(project_node)
    ```

If a path is ambiguous or not found, a `NotFoundError` will be raised.

## Usage

### Getting Started

```python
import os
from workflowy_py import WorkflowyClient

# Initialize the client. It will discover the token automatically.
# Make sure your token is set in one of the supported locations.
client = WorkflowyClient()

# Get the root node (your main Workflowy page)
root = client.get_node("root")
print(f"Root node name: {root.name}")
```

### Listing Nodes

You can list the children of any node.

```python
# List children of a specific project by its path
children = client.list_nodes("Projects/My Project/Tasks")

for child in children:
    print(f"- {child.name} (ID: {child.id})")
```

### Creating Nodes

Create new nodes under a parent. You can specify the position (`"top"`, `"bottom"`, or an integer index).

```python
# Create a new node at the top of a project list
new_task = client.create_node("Projects/My Project/Tasks", "New Task from API")
print(f"Created task: '{new_task.name}'")

# You can also create a node using a parent Node object
project_node = client.get_node("Projects/My Project")
new_task_with_note = client.create_node(
    project_node,
    "Another Task",
    position="bottom",
    note="This is a note for the task."
)
print(f"Created task: '{new_task_with_note.name}' with note.")
```

### Updating Nodes

Update a node's name, note, or other properties.

```python
updated_node = client.update_node(
    "Projects/My Project/Tasks/New Task from API",
    name="Updated Task Name",
    note="This note has been updated."
)
print(f"Node updated. New name: '{updated_node.name}'")
```

### Completing and Uncompleting Nodes

```python
# Complete the task by its path
client.complete_node("Projects/My Project/Tasks/Updated Task Name")
print(f"Task completed.")

# Uncomplete it again
client.uncomplete_node("Projects/My Project/Tasks/Updated Task Name")
print(f"Task uncompleted.")
```

### Deleting Nodes

```python
# Delete one of the tasks we created
client.delete_node("Projects/My Project/Another Task")
print(f"Task deleted.")
```

### Finding Nodes

The client provides two primary ways to find a specific node if you don't already have its ID.

#### By Path

The `find_node_by_path` method is the most common way to locate a node.

```python
try:
    project_node = client.find_node_by_path("Projects/My Project")
    print(f"Found project: {project_node.name}")
except NotFoundError:
    print("Project not found!")
```

#### By Partial ID from URL

If you have the partial ID from a Workflowy URL, you can perform a recursive search to find the full node. See the `examples/find_by_partial_id.py` script for a detailed implementation.

### Error Handling

The client raises specific exceptions for different types of errors:
- `AuthError`: Invalid or missing token (401)
- `NotFoundError`: Node not found (404)
- `RateLimitError`: Rate limit exceeded (429)
- `ClientError`: Other 4xx errors
- `ServerError`: 5xx errors

```python
from workflowy_py.errors import NotFoundError

try:
    client.get_node("Projects/Non-Existent Project")
except NotFoundError:
    print("Caught expected error: Node not found!")
```
