"""Unit tests for BookService (book.py service + repository)."""
import pytest
from app.repositories.book import BookRepository
from app.services.book import BookService
from app.schemas.book import BookCreate, BookUpdate


def _svc() -> BookService:
    return BookService(repo=BookRepository())


def _book_create(**kwargs) -> BookCreate:
    defaults = dict(title="The Hobbit", author="J.R.R. Tolkien", total_copies=2)
    defaults.update(kwargs)
    return BookCreate(**defaults)


# ── create_book ─────────────────────────────────────────────────────────────

class TestCreateBook:
    async def test_creates_and_returns_book(self, init_db):
        book = await _svc().create_book(_book_create())
        assert book.id is not None
        assert book.title == "The Hobbit"
        assert book.author == "J.R.R. Tolkien"

    async def test_available_copies_equals_total_copies(self, init_db):
        book = await _svc().create_book(_book_create(total_copies=5))
        assert book.available_copies == 5

    async def test_optional_fields_default_to_none(self, init_db):
        book = await _svc().create_book(_book_create())
        assert book.isbn is None
        assert book.genre is None
        assert book.publisher is None


# ── get_book ────────────────────────────────────────────────────────────────

class TestGetBook:
    async def test_returns_existing_book(self, init_db):
        svc = _svc()
        created = await svc.create_book(_book_create())
        fetched = await svc.get_book(created.id)
        assert fetched is not None
        assert fetched.id == created.id

    async def test_returns_none_for_missing_id(self, init_db):
        result = await _svc().get_book(99999)
        assert result is None


# ── get_books ────────────────────────────────────────────────────────────────

class TestGetBooks:
    async def test_returns_all_books(self, init_db):
        svc = _svc()
        for i in range(3):
            await svc.create_book(_book_create(title=f"Book {i}"))
        books, total = await svc.get_books()
        assert total == 3
        assert len(books) == 3

    async def test_search_by_title(self, init_db):
        svc = _svc()
        await svc.create_book(_book_create(title="Dune"))
        await svc.create_book(_book_create(title="Foundation"))
        books, total = await svc.get_books(search="dune")
        assert total == 1
        assert books[0].title == "Dune"

    async def test_search_by_author(self, init_db):
        svc = _svc()
        await svc.create_book(_book_create(author="Asimov"))
        await svc.create_book(_book_create(author="Herbert"))
        books, total = await svc.get_books(search="asimov")
        assert total == 1

    async def test_filter_by_genre(self, init_db):
        svc = _svc()
        await svc.create_book(_book_create(genre="Sci-Fi"))
        await svc.create_book(_book_create(genre="Fantasy"))
        books, total = await svc.get_books(genre="sci-fi")
        assert total == 1

    async def test_pagination(self, init_db):
        svc = _svc()
        for i in range(5):
            await svc.create_book(_book_create(title=f"Book {i}"))
        books, total = await svc.get_books(page=1, size=2)
        assert total == 5
        assert len(books) == 2

    async def test_empty_library_returns_zero(self, init_db):
        books, total = await _svc().get_books()
        assert total == 0
        assert books == []


# ── update_book ───────────────────────────────────────────────────────────────

class TestUpdateBook:
    async def test_updates_title(self, init_db):
        svc = _svc()
        book = await svc.create_book(_book_create())
        updated = await svc.update_book(book.id, BookUpdate(title="Updated Title"))
        assert updated.title == "Updated Title"
        assert updated.author == "J.R.R. Tolkien"

    async def test_increases_available_copies_when_total_increases(self, init_db):
        svc = _svc()
        book = await svc.create_book(_book_create(total_copies=2))
        updated = await svc.update_book(book.id, BookUpdate(total_copies=4))
        assert updated.available_copies == 4

    async def test_decreases_available_copies_when_total_decreases(self, init_db):
        svc = _svc()
        book = await svc.create_book(_book_create(total_copies=4))
        updated = await svc.update_book(book.id, BookUpdate(total_copies=2))
        assert updated.available_copies == 2

    async def test_returns_none_for_missing_book(self, init_db):
        result = await _svc().update_book(99999, BookUpdate(title="X"))
        assert result is None


# ── delete_book ───────────────────────────────────────────────────────────────

class TestDeleteBook:
    async def test_deletes_existing_book(self, init_db):
        svc = _svc()
        book = await svc.create_book(_book_create())
        deleted = await svc.delete_book(book.id)
        assert deleted is True
        assert await svc.get_book(book.id) is None

    async def test_returns_false_for_missing_book(self, init_db):
        result = await _svc().delete_book(99999)
        assert result is False
