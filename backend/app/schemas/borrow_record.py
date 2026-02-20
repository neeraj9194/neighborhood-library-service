from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class BorrowRequest(BaseModel):
    """Schema for borrowing a book."""
    book_id: int = Field(..., description="ID of the book to borrow")
    member_id: int = Field(..., description="ID of the member borrowing the book")
    borrow_days: int | None = Field(None, ge=1, le=90, description="Number of days to borrow (default: 14)")


class BorrowRecordResponse(BaseModel):
    """Schema for borrow record API responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    member_id: int
    borrowed_at: datetime
    due_date: datetime
    returned_at: datetime | None
    status: str

    # Nested book and member info
    book_title: str | None = None
    book_author: str | None = None
    member_name: str | None = None
    member_email: str | None = None


class BorrowRecordListResponse(BaseModel):
    """Paginated borrow record list response."""
    items: list[BorrowRecordResponse]
    total: int
    page: int
    size: int
