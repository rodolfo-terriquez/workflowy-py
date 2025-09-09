from __future__ import annotations

from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class Node(BaseModel):
    id: str
    name: str
    note: Optional[str] = None
    priority: int
    data: dict[str, Any] = Field(default_factory=dict)
    created_at: int = Field(alias="createdAt")
    modified_at: int = Field(alias="modifiedAt")
    completed_at: Optional[int] = Field(alias="completedAt", default=None)


class CreateNodePayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    parent_id: Optional[str] = None
    name: str
    position: Optional[Union[Literal["top", "bottom"], int]] = "top"
    note: Optional[str] = None


class UpdateNodePayload(BaseModel):
    name: Optional[str] = None
    note: Optional[str] = None
    priority: Optional[int] = None
    data: Optional[dict[str, Any]] = None


class CreateNodeResponse(BaseModel):
    item_id: str


class GetNodeResponse(BaseModel):
    node: Node


class ListNodesResponse(BaseModel):
    nodes: list[Node]
