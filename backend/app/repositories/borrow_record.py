"""BorrowRecord repository — pure database access, no business logic."""
import logging
from datetime import datetime, timezone

from app.models.borrow_record import BorrowRecord, BorrowStatus

logger = logging.getLogger(__name__)


class BorrowRecordRepository:
    async def create(
        self,
        *,
        book_id: int,
        member_id: int,
        due_date: datetime,
    ) -> BorrowRecord:
        logger.debug(
            "Inserting borrow record: book_id=%s, member_id=%s, due_date=%s",
            book_id, member_id, due_date,
        )
        record = await BorrowRecord.create(
            book_id=book_id,
            member_id=member_id,
            borrowed_at=datetime.now(timezone.utc),
            due_date=due_date,
            status=BorrowStatus.BORROWED,
        )
        await record.fetch_related("book", "member")
        logger.debug("Inserted borrow record: id=%s", record.id)
        return record

    async def get_by_id(self, record_id: int) -> BorrowRecord | None:
        logger.debug("Fetching borrow record: id=%s", record_id)
        record = await (
            BorrowRecord.get_or_none(id=record_id)
            .prefetch_related("book", "member")
        )
        logger.debug("Fetch result: id=%s found=%s", record_id, record is not None)
        return record

    async def get_all(
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
        qs = BorrowRecord.all().prefetch_related("book", "member")
        if member_id is not None:
            qs = qs.filter(member_id=member_id)
        if book_id is not None:
            qs = qs.filter(book_id=book_id)
        if status:
            qs = qs.filter(status=status)
        total = await qs.count()
        records = await qs.offset((page - 1) * size).limit(size)
        logger.debug("Listed borrow records: total=%d, returned=%d", total, len(records))
        return records, total

    async def get_overdue(
        self,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[BorrowRecord], int]:
        now = datetime.now(timezone.utc)
        logger.debug("Fetching overdue records: page=%d, size=%d, cutoff=%s", page, size, now)
        qs = BorrowRecord.filter(
            status__in=[BorrowStatus.BORROWED, BorrowStatus.OVERDUE],
            due_date__lt=now,
        ).prefetch_related("book", "member")
        total = await qs.count()
        records = await qs.offset((page - 1) * size).limit(size)
        logger.debug("Overdue records: total=%d, returned=%d", total, len(records))
        return records, total

    async def count_active_for_member(self, member_id: int) -> int:
        count = await BorrowRecord.filter(
            member_id=member_id,
            status__in=[BorrowStatus.BORROWED, BorrowStatus.OVERDUE],
        ).count()
        logger.debug("Active borrow count for member_id=%s: %d", member_id, count)
        return count

    async def get_active_for_member(self, member_id: int) -> list[BorrowRecord]:
        logger.debug("Fetching active borrows for member_id=%s", member_id)
        records = await (
            BorrowRecord.filter(
                member_id=member_id,
                status__in=[BorrowStatus.BORROWED, BorrowStatus.OVERDUE],
            )
            .prefetch_related("book", "member")
            .order_by("due_date")
        )
        logger.debug("Active borrows for member_id=%s: count=%d", member_id, len(records))
        return records

    async def find_active_borrow(self, book_id: int, member_id: int) -> BorrowRecord | None:
        logger.debug("Checking for active borrow: book_id=%s, member_id=%s", book_id, member_id)
        record = await BorrowRecord.filter(
            book_id=book_id,
            member_id=member_id,
            status=BorrowStatus.BORROWED,
        ).first()
        logger.debug(
            "Active borrow check: book_id=%s, member_id=%s, exists=%s",
            book_id, member_id, record is not None,
        )
        return record

    async def save(self, record: BorrowRecord) -> BorrowRecord:
        logger.debug("Saving borrow record: id=%s, status=%s", record.id, record.status)
        await record.save()
        return record
