"""Pydantic models for Flock Energy API data structures."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class Meter(BaseModel):
    """Represents a utility meter."""

    id: Optional[str] = None
    meter_id: Optional[str] = None
    name: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[dict[str, Any]] = Field(default_factory=dict)


class Transformer(BaseModel):
    """Represents a transformer asset."""

    id: Optional[str] = None
    transformer_id: Optional[str] = None
    name: Optional[str] = None
    capacity: Optional[float] = None
    location: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[dict[str, Any]] = Field(default_factory=dict)


class Hierarchy(BaseModel):
    """Represents a hierarchy node in the energy network."""

    id: Optional[str] = None
    parent_id: Optional[str] = None
    name: Optional[str] = None
    level: Optional[str] = None
    children: Optional[list["Hierarchy"]] = Field(default_factory=list)
    metadata: Optional[dict[str, Any]] = Field(default_factory=dict)

