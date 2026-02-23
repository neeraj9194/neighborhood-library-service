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
        logger.info(
            "Borrow requested: book_id=%s, member_id=%s, borrow_days=%s (resolved=%d)",
            book_id, member_id, borrow_days, days,
        )

        async with in_transaction():
            logger.debug("Transaction started for borrow: book_id=%s, member_id=%s", book_id, member_id)

            # Lock the book row to prevent concurrent modifications
            book = await self._books.get_by_id_for_update(book_id)
            if not book:
                logger.warning("Borrow failed: book_id=%s not found", book_id)
                raise BorrowError("Book not found", status_code=404)

            logger.debug(
                "Book locked: id=%s, title='%s', available_copies=%d, total_copies=%d",
                book.id, book.title, book.available_copies, book.total_copies,
            )

            if book.available_copies <= 0:
                logger.warning(
                    "Borrow failed: no copies available for book_id=%s ('%s'), "
                    "available=%d, total=%d",
                    book_id, book.title, book.available_copies, book.total_copies,
                )
                raise BorrowError("No copies available for this book")

            member = await self._members.get_by_id(member_id)
            if not member:
                logger.warning("Borrow failed: member_id=%s not found", member_id)
                raise BorrowError("Member not found", status_code=404)

            logger.debug(
                "Member found: id=%s, name='%s', is_active=%s",
                member.id, member.name, member.is_active,
            )

            if not member.is_active:
                logger.warning(
                    "Borrow failed: member_id=%s ('%s') is inactive",
                    member_id, member.name,
                )
                raise BorrowError("Member account is inactive")

            active_count = await self._borrow.count_active_for_member(member_id)
            logger.debug(
                "Active borrow count for member_id=%s: %d (limit=%d)",
                member_id, active_count, MAX_ACTIVE_BORROWS_PER_MEMBER,
            )
            if active_count >= MAX_ACTIVE_BORROWS_PER_MEMBER:
                logger.warning(
                    "Borrow failed: member_id=%s has %d active borrows (limit %d)",
                    member_id, active_count, MAX_ACTIVE_BORROWS_PER_MEMBER,
                )
                raise BorrowError(
                    f"Borrow limit reached: a member may hold at most "
                    f"{MAX_ACTIVE_BORROWS_PER_MEMBER} books at a time "
                    f"(currently {active_count} active)"
                )

            existing = await self._borrow.find_active_borrow(book_id, member_id)
            if existing:
                logger.warning(
                    "Borrow failed: member_id=%s already has book_id=%s borrowed (record_id=%s)",
                    member_id, book_id, existing.id,
                )
                raise BorrowError("Member already has this book borrowed")

            due_date = datetime.now(timezone.utc) + timedelta(days=days)
            logger.debug("Creating borrow record: due_date=%s", due_date)

            record = await self._borrow.create(
                book_id=book_id,
                member_id=member_id,
                due_date=due_date,
            )

            book.available_copies -= 1
            await self._books.update(book, {"available_copies": book.available_copies})

            logger.debug(
                "Copies decremented: book_id=%s, available_copies=%d -> %d",
                book_id, book.available_copies + 1, book.available_copies,
            )

        logger.info(
            "Book borrowed: record_id=%s, book_id=%s ('%s'), member_id=%s ('%s'), "
            "due=%s, remaining_copies=%d",
            record.id, book_id, book.title, member_id, member.name,
            due_date.date(), book.available_copies,
        )
        return record

    async def return_book(self, record_id: int) -> BorrowRecord:
        """Record the return of a borrowed book.

        Uses a transaction with row-level locking on the book to safely
        increment ``available_copies``.
        """
        logger.info("Return requested: record_id=%s", record_id)

        async with in_transaction():
            logger.debug("Transaction started for return: record_id=%s", record_id)

            record = await self._borrow.get_by_id(record_id)
            if not record:
                logger.warning("Return failed: record_id=%s not found", record_id)
                raise BorrowError("Borrow record not found", status_code=404)

            logger.debug(
                "Borrow record found: id=%s, book_id=%s, member_id=%s, status=%s, due_date=%s",
                record.id, record.book_id, record.member_id, record.status, record.due_date,
            )

            if record.status == BorrowStatus.RETURNED:
                logger.warning(
                    "Return failed: record_id=%s already returned at %s",
                    record_id, record.returned_at,
                )
                raise BorrowError("This book has already been returned")

            now = datetime.now(timezone.utc)
            is_overdue = record.due_date < now
            record.returned_at = now
            record.status = BorrowStatus.RETURNED
            await self._borrow.save(record)

            logger.debug(
                "Record marked returned: id=%s, returned_at=%s, was_overdue=%s",
                record.id, record.returned_at, is_overdue,
            )

            # Lock the book row before incrementing copies
            book = await self._books.get_by_id_for_update(record.book_id)
            if book:
                old_copies = book.available_copies
                new_copies = min(book.available_copies + 1, book.total_copies)
                await self._books.update(book, {"available_copies": new_copies})
                logger.debug(
                    "Copies incremented: book_id=%s, available_copies=%d -> %d",
                    record.book_id, old_copies, new_copies,
                )
            else:
                logger.warning(
                    "Return: book_id=%s not found when incrementing copies", record.book_id
                )

        logger.info(
            "Book returned: record_id=%s, book_id=%s, member_id=%s, was_overdue=%s",
            record_id, record.book_id, record.member_id, is_overdue,
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
        logger.debug(
            "Listing borrow records: page=%d, size=%d, member_id=%s, book_id=%s, status=%s",
            page, size, member_id, book_id, status,
        )
        records, total = await self._borrow.get_all(
            page=page, size=size, member_id=member_id, book_id=book_id, status=status
        )
        logger.info("Borrow records listed: total=%d, returned=%d", total, len(records))
        return records, total

    async def get_overdue_records(
        self,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[BorrowRecord], int]:
        logger.debug("Fetching overdue records: page=%d, size=%d", page, size)
        records, total = await self._borrow.get_overdue(page=page, size=size)
        logger.info("Overdue records fetched: total=%d, returned=%d", total, len(records))
        return records, total

    async def get_member_borrowed_books(self, member_id: int) -> list[BorrowRecord]:
        logger.debug("Fetching borrowed books for member_id=%s", member_id)
        member = await self._members.get_by_id(member_id)
        if not member:
            logger.warning("Member borrowed books: member_id=%s not found", member_id)
            raise BorrowError("Member not found", status_code=404)
        records = await self._borrow.get_active_for_member(member_id)
        logger.info(
            "Member borrowed books: member_id=%s ('%s'), active_count=%d",
            member_id, member.name, len(records),
        )
        return records
