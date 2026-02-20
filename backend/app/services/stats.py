"""Stats service — aggregated library metrics."""
from datetime import datetime, timezone

from tortoise.functions import Sum, Count

from app.models.book import Book
from app.models.borrow_record import BorrowRecord, BorrowStatus
from app.models.member import Member
from app.schemas.stats import StatsResponse


class StatsService:
    async def get_stats(self) -> StatsResponse:
        # Book aggregate
        book_agg = await Book.all().annotate(
            total_copies_sum=Sum("total_copies"),
            available_copies_sum=Sum("available_copies"),
        ).values("total_copies_sum", "available_copies_sum")
        total_books = await Book.all().count()
        total_copies = book_agg[0]["total_copies_sum"] or 0 if book_agg else 0
        available_copies = book_agg[0]["available_copies_sum"] or 0 if book_agg else 0

        # Members
        total_members = await Member.all().count()
        active_members = await Member.filter(is_active=True).count()

        # Borrows
        borrowed_copies = await BorrowRecord.filter(status=BorrowStatus.BORROWED).count()
        overdue_count = await BorrowRecord.filter(
            status__in=[BorrowStatus.BORROWED, BorrowStatus.OVERDUE],
            due_date__lt=datetime.now(timezone.utc),
        ).count()

        return StatsResponse(
            total_books=total_books,
            total_copies=total_copies,
            available_copies=available_copies,
            borrowed_copies=borrowed_copies,
            total_members=total_members,
            active_members=active_members,
            overdue_count=overdue_count,
        )
