from typing import List, Optional

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """
    Represents one structured error produced by the backend.
    """

    code: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Machine-readable error code.",
    )

    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Human-readable description of the error.",
    )

    field: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Request field associated with the error, if applicable.",
    )


class ErrorResponse(BaseModel):
    """
    Standard error response returned by the backend API.
    """

    success: bool = Field(
        default=False,
        description="Always false for an error response.",
    )

    message: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="High-level description of the failure.",
    )

    errors: List[ErrorDetail] = Field(
        default_factory=list,
        description="Detailed errors associated with the failure.",
    )