"""BorrowRecord repository — pure database access, no business logic."""
from datetime import datetime, timezone

from app.models.borrow_record import BorrowRecord, BorrowStatus


class BorrowRecordRepository:
    async def create(
        self,
        *,
        book_id: int,
        member_id: int,
        due_date: datetime,
    ) -> BorrowRecord:
        record = await BorrowRecord.create(
            book_id=book_id,
            member_id=member_id,
            borrowed_at=datetime.now(timezone.utc),
            due_date=due_date,
            status=BorrowStatus.BORROWED,
        )
        await record.fetch_related("book", "member")
        return record

    async def get_by_id(self, record_id: int) -> BorrowRecord | None:
        return await (
            BorrowRecord.get_or_none(id=record_id)
            .prefetch_related("book", "member")
        )

    async def get_all(
        self,
        page: int = 1,
        size: int = 20,
        member_id: int | None = None,
        book_id: int | None = None,
        status: str | None = None,
    ) -> tuple[list[BorrowRecord], int]:
        qs = BorrowRecord.all().prefetch_related("book", "member")
        if member_id is not None:
            qs = qs.filter(member_id=member_id)
        if book_id is not None:
            qs = qs.filter(book_id=book_id)
        if status:
            qs = qs.filter(status=status)
        total = await qs.count()
        records = await qs.offset((page - 1) * size).limit(size)
        return records, total

    async def get_overdue(
        self,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[BorrowRecord], int]:
        now = datetime.now(timezone.utc)
        qs = BorrowRecord.filter(
            status=BorrowStatus.BORROWED,
            due_date__lt=now,
        ).prefetch_related("book", "member")
        total = await qs.count()
        records = await qs.offset((page - 1) * size).limit(size)
        return records, total

    async def count_active_for_member(self, member_id: int) -> int:
        return await BorrowRecord.filter(
            member_id=member_id,
            status__in=[BorrowStatus.BORROWED, BorrowStatus.OVERDUE],
        ).count()

    async def get_active_for_member(self, member_id: int) -> list[BorrowRecord]:
        return await (
            BorrowRecord.filter(
                member_id=member_id,
                status__in=[BorrowStatus.BORROWED, BorrowStatus.OVERDUE],
            )
            .prefetch_related("book", "member")
            .order_by("due_date")
        )

    async def find_active_borrow(self, book_id: int, member_id: int) -> BorrowRecord | None:
        return await BorrowRecord.filter(
            book_id=book_id,
            member_id=member_id,
            status=BorrowStatus.BORROWED,
        ).first()

    async def save(self, record: BorrowRecord) -> BorrowRecord:
        await record.save()
        return record
