"""Borrow service — all borrow/return business logic."""
from datetime import datetime, timedelta, timezone

from app.core.config import get_settings
from app.models.book import Book
from app.models.borrow_record import BorrowRecord, BorrowStatus
from app.repositories.book import BookRepository
from app.repositories.borrow_record import BorrowRecordRepository
from app.repositories.member import MemberRepository

# Maximum number of books a member may have borrowed simultaneously.
MAX_ACTIVE_BORROWS_PER_MEMBER = 10


class BorrowError(Exception):
    """Raised when a borrow/return operation violates a business rule."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class BorrowService:
    def __init__(
        self,
        borrow_repo: BorrowRecordRepository,
        book_repo: BookRepository,
        member_repo: MemberRepository,
    ) -> None:
        self._borrow = borrow_repo
        self._books = book_repo
        self._members = member_repo

    async def borrow_book(
        self,
        book_id: int,
        member_id: int,
        borrow_days: int | None = None,
    ) -> BorrowRecord:
        settings = get_settings()
        days = borrow_days or settings.DEFAULT_BORROW_DAYS

        book = await self._books.get_by_id(book_id)
        if not book:
            raise BorrowError("Book not found", status_code=404)
        if book.available_copies <= 0:
            raise BorrowError("No copies available for this book")

        member = await self._members.get_by_id(member_id)
        if not member:
            raise BorrowError("Member not found", status_code=404)
        if not member.is_active:
            raise BorrowError("Member account is inactive")

        active_count = await self._borrow.count_active_for_member(member_id)
        if active_count >= MAX_ACTIVE_BORROWS_PER_MEMBER:
            raise BorrowError(
                f"Borrow limit reached: a member may hold at most "
                f"{MAX_ACTIVE_BORROWS_PER_MEMBER} books at a time "
                f"(currently {active_count} active)"
            )

        existing = await self._borrow.find_active_borrow(book_id, member_id)
        if existing:
            raise BorrowError("Member already has this book borrowed")

        due_date = datetime.now(timezone.utc) + timedelta(days=days)
        record = await self._borrow.create(
            book_id=book_id,
            member_id=member_id,
            due_date=due_date,
        )

        book.available_copies -= 1
        await self._books.update(book, {"available_copies": book.available_copies})

        return record

    async def return_book(self, record_id: int) -> BorrowRecord:
        record = await self._borrow.get_by_id(record_id)
        if not record:
            raise BorrowError("Borrow record not found", status_code=404)
        if record.status == BorrowStatus.RETURNED:
            raise BorrowError("This book has already been returned")

        record.returned_at = datetime.now(timezone.utc)
        record.status = BorrowStatus.RETURNED
        await self._borrow.save(record)

        book = await self._books.get_by_id(record.book_id)
        if book:
            new_copies = min(book.available_copies + 1, book.total_copies)
            await self._books.update(book, {"available_copies": new_copies})

        return record

    async def get_borrow_records(
        self,
        page: int = 1,
        size: int = 20,
        member_id: int | None = None,
        book_id: int | None = None,
        status: str | None = None,
    ) -> tuple[list[BorrowRecord], int]:
        return await self._borrow.get_all(
            page=page, size=size, member_id=member_id, book_id=book_id, status=status
        )

    async def get_overdue_records(
        self,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[BorrowRecord], int]:
        records, total = await self._borrow.get_overdue(page=page, size=size)

        # Mark newly-overdue records
        for record in records:
            if record.status != BorrowStatus.OVERDUE:
                record.status = BorrowStatus.OVERDUE
                await self._borrow.save(record)

        return records, total

    async def get_member_borrowed_books(self, member_id: int) -> list[BorrowRecord]:
        member = await self._members.get_by_id(member_id)
        if not member:
            raise BorrowError("Member not found", status_code=404)
        return await self._borrow.get_active_for_member(member_id)
