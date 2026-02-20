"""Book service — business logic that sits between routes and the repository."""
from app.models.book import Book
from app.repositories.book import BookRepository
from app.schemas.book import BookCreate, BookUpdate


class BookService:
    def __init__(self, repo: BookRepository) -> None:
        self._repo = repo

    async def create_book(self, data: BookCreate) -> Book:
        return await self._repo.create(data)

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
        book = await self._repo.get_by_id(book_id)
        if not book:
            return None

        update_dict = data.model_dump(exclude_unset=True)

        # Adjust available_copies proportionally when total_copies changes
        if "total_copies" in update_dict:
            copies_diff = update_dict["total_copies"] - book.total_copies
            update_dict["available_copies"] = max(0, book.available_copies + copies_diff)

        return await self._repo.update(book, update_dict)

    async def delete_book(self, book_id: int) -> bool:
        return await self._repo.delete(book_id)
