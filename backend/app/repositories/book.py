"""Book repository — pure database access, no business logic."""
import logging

from tortoise.expressions import Q

from app.models.book import Book
from app.schemas.book import BookCreate

logger = logging.getLogger(__name__)


class BookRepository:
    async def create(self, data: BookCreate) -> Book:
        logger.debug("Inserting book: title='%s', author='%s', copies=%d", data.title, data.author, data.total_copies)
        book = await Book.create(
            **data.model_dump(),
            available_copies=data.total_copies,
        )
        logger.debug("Inserted book: id=%s", book.id)
        return book

    async def get_by_id(self, book_id: int) -> Book | None:
        logger.debug("Fetching book: id=%s", book_id)
        book = await Book.get_or_none(id=book_id)
        logger.debug("Fetch result: id=%s found=%s", book_id, book is not None)
        return book

    async def get_by_id_for_update(self, book_id: int) -> Book | None:
        """Fetch a book with a row-level lock (SELECT ... FOR UPDATE).

        Must be called inside a transaction. The lock is held until the
        transaction commits or rolls back, preventing concurrent updates
        to ``available_copies``.
        """
        logger.debug("Fetching book with row lock: id=%s", book_id)
        book = await Book.select_for_update().filter(id=book_id).first()
        logger.debug("Locked fetch result: id=%s found=%s", book_id, book is not None)
        return book

    async def get_all(
        self,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
        genre: str | None = None,
    ) -> tuple[list[Book], int]:
        logger.debug("Listing books: page=%d, size=%d, search=%s, genre=%s", page, size, search, genre)
        qs = Book.all()
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(author__icontains=search))
        if genre:
            qs = qs.filter(genre__icontains=genre)
        total = await qs.count()
        books = await qs.offset((page - 1) * size).limit(size)
        logger.debug("Listed books: total=%d, returned=%d", total, len(books))
        return books, total

    async def update(self, book: Book, data: dict) -> Book:
        logger.debug("Updating book: id=%s, fields=%s", book.id, data)
        await book.update_from_dict(data).save()
        logger.debug("Updated book: id=%s", book.id)
        return book

    async def delete(self, book_id: int) -> bool:
        logger.debug("Deleting book: id=%s", book_id)
        deleted = await Book.filter(id=book_id).delete()
        logger.debug("Delete result: id=%s, rows_deleted=%d", book_id, deleted)
        return deleted > 0
