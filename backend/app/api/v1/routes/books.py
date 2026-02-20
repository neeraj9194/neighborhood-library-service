"""Books router — HTTP layer only. Delegates all logic to BookService."""
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.v1.dependencies import get_book_service
from app.schemas.book import BookCreate, BookUpdate, BookResponse, BookListResponse
from app.services.book import BookService

router = APIRouter(prefix="/api/v1/books", tags=["Books"])


@router.post("/", response_model=BookResponse, status_code=201, summary="Create a new book")
async def create_book(
    data: BookCreate,
    svc: BookService = Depends(get_book_service),
):
    """Create a new book record in the library."""
    try:
        book = await svc.create_book(data)
        return BookResponse.model_validate(book, from_attributes=True)
    except Exception as e:
        if "unique" in str(e).lower():
            raise HTTPException(status_code=409, detail="A book with this ISBN already exists")
        raise HTTPException(status_code=500, detail=f"Failed to create book: {e}")


@router.get("/", response_model=BookListResponse, summary="List all books")
async def list_books(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Search by title or author"),
    genre: str | None = Query(None, description="Filter by genre"),
    svc: BookService = Depends(get_book_service),
):
    """List all books with optional search and genre filter. Results are paginated."""
    books, total = await svc.get_books(page=page, size=size, search=search, genre=genre)
    return BookListResponse(
        items=[BookResponse.model_validate(b, from_attributes=True) for b in books],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{book_id}", response_model=BookResponse, summary="Get a book by ID")
async def get_book(
    book_id: int,
    svc: BookService = Depends(get_book_service),
):
    """Get detailed information about a specific book."""
    book = await svc.get_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return BookResponse.model_validate(book, from_attributes=True)


@router.patch("/{book_id}", response_model=BookResponse, summary="Update a book")
async def update_book(
    book_id: int,
    data: BookUpdate,
    svc: BookService = Depends(get_book_service),
):
    """Update an existing book's details. Only provided fields will be updated."""
    book = await svc.update_book(book_id, data)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return BookResponse.model_validate(book, from_attributes=True)


@router.delete("/{book_id}", status_code=204, summary="Delete a book")
async def delete_book(
    book_id: int,
    svc: BookService = Depends(get_book_service),
):
    """Delete a book from the library."""
    if not await svc.delete_book(book_id):
        raise HTTPException(status_code=404, detail="Book not found")
