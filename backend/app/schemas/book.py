from datetime import datetime
import re

from pydantic import BaseModel, Field, ConfigDict, field_validator


_ISBN_10_RE = re.compile(r"^\d{9}[\dX]$")
_ISBN_13_RE = re.compile(r"^\d{13}$")


class BookBase(BaseModel):
    """Shared properties for book creation and updates."""
    title: str = Field(..., min_length=1, max_length=255, examples=["The Great Gatsby"])
    author: str = Field(..., min_length=1, max_length=255, examples=["F. Scott Fitzgerald"])
    isbn: str | None = Field(None, max_length=13, examples=["9780743273565"])
    genre: str | None = Field(None, max_length=100, examples=["Fiction"])
    publisher: str | None = Field(None, max_length=255, examples=["Scribner"])
    total_copies: int = Field(1, ge=1, examples=[3])

    @field_validator("title", "author", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("isbn", mode="before")
    @classmethod
    def validate_isbn(cls, v: str | None) -> str | None:
        if v is None:
            return v
        cleaned = v.replace("-", "").replace(" ", "")
        if not (_ISBN_10_RE.match(cleaned) or _ISBN_13_RE.match(cleaned)):
            raise ValueError(
                "ISBN must be a valid ISBN-10 or ISBN-13 "
                "(10 or 13 digits, optionally separated by hyphens)"
            )
        return cleaned


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

    @field_validator("title", "author", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str | None) -> str | None:
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("isbn", mode="before")
    @classmethod
    def validate_isbn(cls, v: str | None) -> str | None:
        if v is None:
            return v
        cleaned = v.replace("-", "").replace(" ", "")
        if not (_ISBN_10_RE.match(cleaned) or _ISBN_13_RE.match(cleaned)):
            raise ValueError(
                "ISBN must be a valid ISBN-10 or ISBN-13 "
                "(10 or 13 digits, optionally separated by hyphens)"
            )
        return cleaned


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
