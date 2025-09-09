# workflowy-py

> **WARNING: USE AT YOUR OWN RISK**
>
> This software is provided "as is", without warranty of any kind. By using this library, you assume full responsibility for any accidental deletion, modification, or corruption of your Workflowy data. It is highly recommended that you create a backup of your data before performing any write operations.

A clean, typed, sync Python client for the [Workflowy API](https://beta.workflowy.com/api-reference/).

## Installation

This package is not published on PyPI. To install it, you must clone the repository and install it from the local files:

```bash
git clone https://github.com/rodolfo-terriquez/workflowy-py.git
cd workflowy-py
pip install .
```

## Authentication

The client discovers the API token in the following order:
1.  Directly passed to the client: `WorkflowyClient(api_token="YOUR_TOKEN")`
2.  Environment variable: `WORKFLOWY_API_TOKEN`
3.  Configuration file: `~/.workflowy/config` (a plain text file with your token)

If no token is found, an `AuthError` is raised.

## Targeting Nodes

All client methods that interact with a specific node (like `get_node`, `update_node`, etc.) accept a flexible `target` argument. Here are the recommended ways to target a node, in order of convenience:

1.  **Partial ID from URL (Recommended)**: This is the easiest and most precise way to target a specific node. Simply click on a node in the Workflowy app and copy the 12-character ID from the URL.
    ```python
    # This ID comes from the URL, e.g., https://workflowy.com/#/b05b8e38b512
    partial_id = "b05b8e38b512"

    # The client will search your account and find the full node automatically
    client.update_node(partial_id, note="This is the easiest way to target a node!")
    ```

2.  **Node Path String**: If you need to find a node programmatically without knowing its ID, a `/`-separated path is the most convenient way. The client will traverse the tree to find it.
    ```python
    client.update_node("Projects/My Project/Tasks", note="An important update.")
    ```

3.  **Full Node ID String**: For maximum precision, you can use the full, unique UUID of a node.
    ```python
    client.get_node("a5ed28fa-c9f6-439a-adcc-762378b295af")
    ```
4.  **Node Object**: If you have already fetched a `Node` object, you can use it directly in other methods.
    ```python
    project_node = client.find_node_by_path("Projects/My Project")
    # Now you can use the object directly
    tasks = client.list_nodes(project_node)
    ```

If a path or partial ID is ambiguous or not found, a `NotFoundError` will be raised.

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

You can now use the 12-character partial ID from a Workflowy URL directly in any method. The client will automatically search your account to find the corresponding node.

```python
try:
    # This ID comes from the node's URL
    node = client.get_node("b05b8e38b512")
    print(f"Found node by partial ID: {node.name}")
except NotFoundError:
    print("Node with that partial ID not found!")
```

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
