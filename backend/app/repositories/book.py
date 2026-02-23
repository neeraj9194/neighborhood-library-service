"""Book repository — pure database access, no business logic."""
from tortoise.expressions import Q

from app.models.book import Book
from app.schemas.book import BookCreate


class BookRepository:
    async def create(self, data: BookCreate) -> Book:
        return await Book.create(
            **data.model_dump(),
            available_copies=data.total_copies,
        )

    async def get_by_id(self, book_id: int) -> Book | None:
        return await Book.get_or_none(id=book_id)

    async def get_by_id_for_update(self, book_id: int) -> Book | None:
        """Fetch a book with a row-level lock (SELECT ... FOR UPDATE).

        Must be called inside a transaction. The lock is held until the
        transaction commits or rolls back, preventing concurrent updates
        to ``available_copies``.
        """
        return await Book.select_for_update().filter(id=book_id).first()

    async def get_all(
        self,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
        genre: str | None = None,
    ) -> tuple[list[Book], int]:
        qs = Book.all()
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(author__icontains=search))
        if genre:
            qs = qs.filter(genre__icontains=genre)
        total = await qs.count()
        books = await qs.offset((page - 1) * size).limit(size)
        return books, total

    async def update(self, book: Book, data: dict) -> Book:
        await book.update_from_dict(data).save()
        return book

    async def delete(self, book_id: int) -> bool:
        deleted = await Book.filter(id=book_id).delete()
        return deleted > 0
