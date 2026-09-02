from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """
    Standard successful/unsuccessful response envelope used by
    the backend API.

    T represents the actual response payload.
    """

    success: bool = Field(
        ...,
        description="Whether the operation completed successfully.",
    )

    message: str = Field(
        ...,
        min_length=1,
        description="Human-readable result message.",
    )

    data: Optional[T] = Field(
        default=None,
        description="Actual response payload when available.",
    )

    error: Optional[str] = Field(
        default=None,
        description="Error information when the operation fails.",
    )