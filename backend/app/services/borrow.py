"""Borrow service — all borrow/return business logic."""
import logging
from datetime import datetime, timedelta, timezone

from tortoise.transactions import in_transaction

from app.core.config import get_settings
from app.models.book import Book
from app.models.borrow_record import BorrowRecord, BorrowStatus
from app.repositories.book import BookRepository
from app.repositories.borrow_record import BorrowRecordRepository
from app.repositories.member import MemberRepository

logger = logging.getLogger(__name__)

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
        """Record a member borrowing a book.

        The entire operation runs inside a database transaction with a
        row-level lock on the book, ensuring that concurrent requests
        cannot over-decrement ``available_copies``.
        """
        settings = get_settings()
        days = borrow_days or settings.DEFAULT_BORROW_DAYS

        async with in_transaction():
            # Lock the book row to prevent concurrent modifications
            book = await self._books.get_by_id_for_update(book_id)
            if not book:
                logger.warning("Borrow failed: book_id=%s not found", book_id)
                raise BorrowError("Book not found", status_code=404)
            if book.available_copies <= 0:
                logger.warning(
                    "Borrow failed: no copies available for book_id=%s ('%s')",
                    book_id,
                    book.title,
                )
                raise BorrowError("No copies available for this book")

            member = await self._members.get_by_id(member_id)
            if not member:
                logger.warning("Borrow failed: member_id=%s not found", member_id)
                raise BorrowError("Member not found", status_code=404)
            if not member.is_active:
                logger.warning(
                    "Borrow failed: member_id=%s ('%s') is inactive",
                    member_id,
                    member.name,
                )
                raise BorrowError("Member account is inactive")

            active_count = await self._borrow.count_active_for_member(member_id)
            if active_count >= MAX_ACTIVE_BORROWS_PER_MEMBER:
                logger.warning(
                    "Borrow failed: member_id=%s has %d active borrows (limit %d)",
                    member_id,
                    active_count,
                    MAX_ACTIVE_BORROWS_PER_MEMBER,
                )
                raise BorrowError(
                    f"Borrow limit reached: a member may hold at most "
                    f"{MAX_ACTIVE_BORROWS_PER_MEMBER} books at a time "
                    f"(currently {active_count} active)"
                )

            existing = await self._borrow.find_active_borrow(book_id, member_id)
            if existing:
                logger.warning(
                    "Borrow failed: member_id=%s already has book_id=%s borrowed",
                    member_id,
                    book_id,
                )
                raise BorrowError("Member already has this book borrowed")

            due_date = datetime.now(timezone.utc) + timedelta(days=days)
            record = await self._borrow.create(
                book_id=book_id,
                member_id=member_id,
                due_date=due_date,
            )

            book.available_copies -= 1
            await self._books.update(book, {"available_copies": book.available_copies})

        logger.info(
            "Book borrowed: record_id=%s, book_id=%s ('%s'), member_id=%s ('%s'), due=%s",
            record.id,
            book_id,
            book.title,
            member_id,
            member.name,
            due_date.date(),
        )
        return record

    async def return_book(self, record_id: int) -> BorrowRecord:
        """Record the return of a borrowed book.

        Uses a transaction with row-level locking on the book to safely
        increment ``available_copies``.
        """
        async with in_transaction():
            record = await self._borrow.get_by_id(record_id)
            if not record:
                logger.warning("Return failed: record_id=%s not found", record_id)
                raise BorrowError("Borrow record not found", status_code=404)
            if record.status == BorrowStatus.RETURNED:
                logger.warning("Return failed: record_id=%s already returned", record_id)
                raise BorrowError("This book has already been returned")

            record.returned_at = datetime.now(timezone.utc)
            record.status = BorrowStatus.RETURNED
            await self._borrow.save(record)

            # Lock the book row before incrementing copies
            book = await self._books.get_by_id_for_update(record.book_id)
            if book:
                new_copies = min(book.available_copies + 1, book.total_copies)
                await self._books.update(book, {"available_copies": new_copies})

        logger.info(
            "Book returned: record_id=%s, book_id=%s, member_id=%s",
            record_id,
            record.book_id,
            record.member_id,
        )
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
        return records, total

    async def get_member_borrowed_books(self, member_id: int) -> list[BorrowRecord]:
        member = await self._members.get_by_id(member_id)
        if not member:
            raise BorrowError("Member not found", status_code=404)
        return await self._borrow.get_active_for_member(member_id)
