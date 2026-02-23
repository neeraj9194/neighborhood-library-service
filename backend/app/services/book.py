"""Book service — business logic that sits between routes and the repository."""
import logging

from tortoise.transactions import in_transaction

from app.models.book import Book
from app.models.borrow_record import BorrowRecord, BorrowStatus
from app.repositories.book import BookRepository
from app.schemas.book import BookCreate, BookUpdate

logger = logging.getLogger(__name__)


class BookService:
    def __init__(self, repo: BookRepository) -> None:
        self._repo = repo

    async def create_book(self, data: BookCreate) -> Book:
        book = await self._repo.create(data)
        logger.info(
            "Book created: id=%s, title='%s', author='%s', copies=%d",
            book.id,
            book.title,
            book.author,
            book.total_copies,
        )
        return book

    async def get_book(self, book_id: int) -> Book | None:
        return await self._repo.get_by_id(book_id)

    async def get_books(
        self,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
        genre: str | None = None,
    ) -> tuple[list[Book], int]:
        return await self._repo.get_all(page=page, size=size, search=search, genre=genre)

    async def update_book(self, book_id: int, data: BookUpdate) -> Book | None:
        async with in_transaction():
            book = await self._repo.get_by_id_for_update(book_id)
            if not book:
                return None

            update_dict = data.model_dump(exclude_unset=True)

            # Adjust available_copies proportionally when total_copies changes
            if "total_copies" in update_dict:
                copies_diff = update_dict["total_copies"] - book.total_copies
                update_dict["available_copies"] = max(0, book.available_copies + copies_diff)

            result = await self._repo.update(book, update_dict)

        logger.info(
            "Book updated: id=%s, fields=%s",
            book_id,
            list(update_dict.keys()),
        )
        return result

    async def delete_book(self, book_id: int) -> bool:
        # Prevent deletion if any active borrows exist
        active_borrows = await BorrowRecord.filter(
            book_id=book_id,
            status__in=[BorrowStatus.BORROWED, BorrowStatus.OVERDUE],
        ).count()
        if active_borrows > 0:
            logger.warning(
                "Delete refused: book_id=%s has %d active borrow(s)",
                book_id,
                active_borrows,
            )
            raise BookDeleteError(
                f"Cannot delete book: {active_borrows} active borrow(s) exist"
            )
        deleted = await self._repo.delete(book_id)
        if deleted:
            logger.info("Book deleted: id=%s", book_id)
        return deleted


class BookDeleteError(Exception):
    """Raised when a book cannot be deleted due to active borrows."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)
