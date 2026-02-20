"""Stats response schema."""
from pydantic import BaseModel


class StatsResponse(BaseModel):
    """Aggregated library statistics."""
    total_books: int
    total_copies: int
    available_copies: int
    borrowed_copies: int
    total_members: int
    active_members: int
    overdue_count: int
