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
        logger.debug(
            "Creating book: title='%s', author='%s', isbn=%s, copies=%d",
            data.title, data.author, data.isbn, data.total_copies,
        )
        book = await self._repo.create(data)
        logger.info(
            "Book created: id=%s, title='%s', author='%s', isbn=%s, copies=%d",
            book.id, book.title, book.author, book.isbn, book.total_copies,
        )
        return book

    async def get_book(self, book_id: int) -> Book | None:
        logger.debug("Getting book: id=%s", book_id)
        book = await self._repo.get_by_id(book_id)
        if book:
            logger.debug("Book found: id=%s, title='%s'", book.id, book.title)
        else:
            logger.debug("Book not found: id=%s", book_id)
        return book

    async def get_books(
        self,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
        genre: str | None = None,
    ) -> tuple[list[Book], int]:
        logger.debug(
            "Listing books: page=%d, size=%d, search=%s, genre=%s",
            page, size, search, genre,
        )
        books, total = await self._repo.get_all(page=page, size=size, search=search, genre=genre)
        logger.info("Books listed: total=%d, returned=%d", total, len(books))
        return books, total

    async def update_book(self, book_id: int, data: BookUpdate) -> Book | None:
        logger.info("Update requested: book_id=%s, fields=%s", book_id, data.model_dump(exclude_unset=True))

        async with in_transaction():
            book = await self._repo.get_by_id_for_update(book_id)
            if not book:
                logger.debug("Update skipped: book_id=%s not found", book_id)
                return None

            update_dict = data.model_dump(exclude_unset=True)

            # Adjust available_copies proportionally when total_copies changes
            if "total_copies" in update_dict:
                old_total = book.total_copies
                old_available = book.available_copies
                copies_diff = update_dict["total_copies"] - old_total
                update_dict["available_copies"] = max(0, old_available + copies_diff)
                logger.debug(
                    "Copies adjustment: book_id=%s, total %d -> %d, available %d -> %d",
                    book_id, old_total, update_dict["total_copies"],
                    old_available, update_dict["available_copies"],
                )

            result = await self._repo.update(book, update_dict)

        logger.info(
            "Book updated: id=%s, fields=%s",
            book_id, list(update_dict.keys()),
        )
        return result

    async def delete_book(self, book_id: int) -> bool:
        logger.info("Delete requested: book_id=%s", book_id)

        # Prevent deletion if any active borrows exist
        active_borrows = await BorrowRecord.filter(
            book_id=book_id,
            status__in=[BorrowStatus.BORROWED, BorrowStatus.OVERDUE],
        ).count()
        logger.debug("Active borrow check for delete: book_id=%s, active=%d", book_id, active_borrows)

        if active_borrows > 0:
            logger.warning(
                "Delete refused: book_id=%s has %d active borrow(s)",
                book_id, active_borrows,
            )
            raise BookDeleteError(
                f"Cannot delete book: {active_borrows} active borrow(s) exist"
            )

        deleted = await self._repo.delete(book_id)
        if deleted:
            logger.info("Book deleted: id=%s", book_id)
        else:
            logger.debug("Delete: book_id=%s not found", book_id)
        return deleted


class BookDeleteError(Exception):
    """Raised when a book cannot be deleted due to active borrows."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)
