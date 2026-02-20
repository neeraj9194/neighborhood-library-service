from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class BookBase(BaseModel):
    """Shared properties for book creation and updates."""
    title: str = Field(..., min_length=1, max_length=255, examples=["The Great Gatsby"])
    author: str = Field(..., min_length=1, max_length=255, examples=["F. Scott Fitzgerald"])
    isbn: str | None = Field(None, max_length=13, examples=["9780743273565"])
    genre: str | None = Field(None, max_length=100, examples=["Fiction"])
    publisher: str | None = Field(None, max_length=255, examples=["Scribner"])
    total_copies: int = Field(1, ge=1, examples=[3])


class BookCreate(BookBase):
    """Schema for creating a new book."""
    pass


class BookUpdate(BaseModel):
    """Schema for updating an existing book. All fields are optional."""
    title: str | None = Field(None, min_length=1, max_length=255)
    author: str | None = Field(None, min_length=1, max_length=255)
    isbn: str | None = Field(None, max_length=13)
    genre: str | None = Field(None, max_length=100)
    publisher: str | None = Field(None, max_length=255)
    total_copies: int | None = Field(None, ge=1)


class BookResponse(BookBase):
    """Schema for book API responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    available_copies: int
    created_at: datetime
    updated_at: datetime


class BookListResponse(BaseModel):
    """Paginated book list response."""
    items: list[BookResponse]
    total: int
    page: int
    size: int
