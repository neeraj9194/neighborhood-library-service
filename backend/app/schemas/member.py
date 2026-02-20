from datetime import datetime

from pydantic import BaseModel, Field, EmailStr, ConfigDict


class MemberBase(BaseModel):
    """Shared properties for member creation and updates."""
    name: str = Field(..., min_length=1, max_length=255, examples=["Jane Doe"])
    email: EmailStr = Field(..., examples=["jane.doe@example.com"])
    phone: str | None = Field(None, max_length=20, examples=["+1-555-0100"])
    address: str | None = Field(None, max_length=500, examples=["123 Oak Street"])


class MemberCreate(MemberBase):
    """Schema for creating a new member."""
    pass


class MemberUpdate(BaseModel):
    """Schema for updating an existing member. All fields are optional."""
    name: str | None = Field(None, min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=20)
    address: str | None = Field(None, max_length=500)
    is_active: bool | None = None


class MemberResponse(MemberBase):
    """Schema for member API responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class MemberListResponse(BaseModel):
    """Paginated member list response."""
    items: list[MemberResponse]
    total: int
    page: int
    size: int
