"""Unit tests for BorrowService (borrow.py service + all 3 repositories)."""
import pytest
from datetime import datetime, timedelta, timezone

from app.repositories.book import BookRepository
from app.repositories.borrow_record import BorrowRecordRepository
from app.repositories.member import MemberRepository
from app.services.borrow import BorrowService, BorrowError
from app.models.borrow_record import BorrowStatus
from app.schemas.book import BookCreate
from app.schemas.member import MemberCreate


def _svc() -> BorrowService:
    return BorrowService(
        borrow_repo=BorrowRecordRepository(),
        book_repo=BookRepository(),
        member_repo=MemberRepository(),
    )


async def _make_book(total_copies=2, **kwargs):
    data = dict(title="Test Book", author="Test Author", total_copies=total_copies)
    data.update(kwargs)
    return await BookRepository().create(BookCreate(**data))


async def _make_member(email="member@example.com", **kwargs):
    data = dict(name="Test Member", email=email)
    data.update(kwargs)
    return await MemberRepository().create(MemberCreate(**data))


# ── borrow_book ───────────────────────────────────────────────────────────────

class TestBorrowBook:
    async def test_creates_borrow_record(self, init_db):
        book = await _make_book()
        member = await _make_member()
        record = await _svc().borrow_book(book.id, member.id)
        assert record.id is not None
        assert record.book_id == book.id
        assert record.member_id == member.id
        assert record.status == BorrowStatus.BORROWED

    async def test_decrements_available_copies(self, init_db):
        book = await _make_book(total_copies=3)
        member = await _make_member()
        await _svc().borrow_book(book.id, member.id)
        await book.refresh_from_db()
        assert book.available_copies == 2

    async def test_custom_borrow_days_sets_due_date(self, init_db):
        book = await _make_book()
        member = await _make_member()
        record = await _svc().borrow_book(book.id, member.id, borrow_days=7)
        expected = datetime.now(timezone.utc) + timedelta(days=7)
        diff = abs((record.due_date - expected).total_seconds())
        assert diff < 5

    async def test_raises_if_book_not_found(self, init_db):
        member = await _make_member()
        with pytest.raises(BorrowError, match="Book not found"):
            await _svc().borrow_book(99999, member.id)

    async def test_raises_if_no_copies_available(self, init_db):
        book = await _make_book(total_copies=1)
        m1 = await _make_member(email="m1@x.com")
        m2 = await _make_member(email="m2@x.com")
        await _svc().borrow_book(book.id, m1.id)
        with pytest.raises(BorrowError, match="No copies available"):
            await _svc().borrow_book(book.id, m2.id)

    async def test_raises_if_member_not_found(self, init_db):
        book = await _make_book()
        with pytest.raises(BorrowError, match="Member not found"):
            await _svc().borrow_book(book.id, 99999)

    async def test_raises_if_member_inactive(self, init_db):
        book = await _make_book()
        member = await _make_member()
        await MemberRepository().update(member, {"is_active": False})
        with pytest.raises(BorrowError, match="inactive"):
            await _svc().borrow_book(book.id, member.id)

    async def test_raises_when_borrow_limit_reached(self, init_db):
        """A member cannot hold more than MAX_ACTIVE_BORROWS_PER_MEMBER books."""
        from app.services.borrow import MAX_ACTIVE_BORROWS_PER_MEMBER
        # One book with enough copies, N+1 different title books to borrow
        member = await _make_member()
        svc = _svc()
        for i in range(MAX_ACTIVE_BORROWS_PER_MEMBER):
            book = await _make_book(total_copies=10, title=f"Limit Test Book {i}")
            await svc.borrow_book(book.id, member.id)
        # 11th borrow should be rejected
        extra_book = await _make_book(total_copies=5, title="One Too Many")
        with pytest.raises(BorrowError, match="Borrow limit reached"):
            await svc.borrow_book(extra_book.id, member.id)

    async def test_raises_if_already_borrowed_same_book(self, init_db):
        book = await _make_book(total_copies=5)
        member = await _make_member()
        svc = _svc()
        await svc.borrow_book(book.id, member.id)
        with pytest.raises(BorrowError, match="already has this book borrowed"):
            await svc.borrow_book(book.id, member.id)


# ── return_book ───────────────────────────────────────────────────────────────

class TestReturnBook:
    async def test_sets_status_to_returned(self, init_db):
        book = await _make_book()
        member = await _make_member()
        svc = _svc()
        record = await svc.borrow_book(book.id, member.id)
        returned = await svc.return_book(record.id)
        assert returned.status == BorrowStatus.RETURNED
        assert returned.returned_at is not None

    async def test_increments_available_copies(self, init_db):
        book = await _make_book(total_copies=2)
        member = await _make_member()
        svc = _svc()
        record = await svc.borrow_book(book.id, member.id)
        await svc.return_book(record.id)
        await book.refresh_from_db()
        assert book.available_copies == 2

    async def test_raises_if_record_not_found(self, init_db):
        with pytest.raises(BorrowError, match="Borrow record not found"):
            await _svc().return_book(99999)

    async def test_raises_if_already_returned(self, init_db):
        book = await _make_book()
        member = await _make_member()
        svc = _svc()
        record = await svc.borrow_book(book.id, member.id)
        await svc.return_book(record.id)
        with pytest.raises(BorrowError, match="already been returned"):
            await svc.return_book(record.id)


# ── get_borrow_records ────────────────────────────────────────────────────────

class TestGetBorrowRecords:
    async def test_returns_all_records(self, init_db):
        book = await _make_book(total_copies=5)
        m1 = await _make_member(email="m1@x.com")
        m2 = await _make_member(email="m2@x.com")
        svc = _svc()
        await svc.borrow_book(book.id, m1.id)
        await svc.borrow_book(book.id, m2.id)
        records, total = await svc.get_borrow_records()
        assert total == 2

    async def test_filter_by_member_id(self, init_db):
        book = await _make_book(total_copies=5)
        m1 = await _make_member(email="m1@x.com")
        m2 = await _make_member(email="m2@x.com")
        svc = _svc()
        await svc.borrow_book(book.id, m1.id)
        await svc.borrow_book(book.id, m2.id)
        records, total = await svc.get_borrow_records(member_id=m1.id)
        assert total == 1
        assert records[0].member_id == m1.id

    async def test_filter_by_status(self, init_db):
        book = await _make_book(total_copies=5)
        m1 = await _make_member(email="m1@x.com")
        m2 = await _make_member(email="m2@x.com")
        svc = _svc()
        r1 = await svc.borrow_book(book.id, m1.id)
        await svc.borrow_book(book.id, m2.id)
        await svc.return_book(r1.id)
        records, total = await svc.get_borrow_records(status=BorrowStatus.RETURNED)
        assert total == 1

    async def test_pagination(self, init_db):
        book = await _make_book(total_copies=10)
        svc = _svc()
        for i in range(5):
            m = await _make_member(email=f"m{i}@x.com")
            await svc.borrow_book(book.id, m.id)
        records, total = await svc.get_borrow_records(page=1, size=2)
        assert total == 5
        assert len(records) == 2


# ── get_member_borrowed_books ─────────────────────────────────────────────────

class TestGetMemberBorrowedBooks:
    async def test_returns_active_borrows(self, init_db):
        book = await _make_book(total_copies=5)
        member = await _make_member()
        svc = _svc()
        await svc.borrow_book(book.id, member.id)
        records = await svc.get_member_borrowed_books(member.id)
        assert len(records) == 1

    async def test_excludes_returned_books(self, init_db):
        book = await _make_book(total_copies=5)
        member = await _make_member()
        svc = _svc()
        record = await svc.borrow_book(book.id, member.id)
        await svc.return_book(record.id)
        records = await svc.get_member_borrowed_books(member.id)
        assert len(records) == 0

    async def test_raises_if_member_not_found(self, init_db):
        with pytest.raises(BorrowError, match="Member not found"):
            await _svc().get_member_borrowed_books(99999)
