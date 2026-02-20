"""Borrow router — HTTP layer only. Delegates all logic to BorrowService."""
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.v1.dependencies import get_borrow_service
from app.schemas.borrow_record import BorrowRequest, BorrowRecordResponse, BorrowRecordListResponse
from app.services.borrow import BorrowService, BorrowError

router = APIRouter(prefix="/api/v1/borrow", tags=["Borrowing"])


def _to_response(record) -> BorrowRecordResponse:
    """Convert a BorrowRecord ORM object to response schema with nested info."""
    return BorrowRecordResponse(
        id=record.id,
        book_id=record.book_id,
        member_id=record.member_id,
        borrowed_at=record.borrowed_at,
        due_date=record.due_date,
        returned_at=record.returned_at,
        status=record.status.value if hasattr(record.status, "value") else record.status,
        book_title=record.book.title if record.book else None,
        book_author=record.book.author if record.book else None,
        member_name=record.member.name if record.member else None,
        member_email=record.member.email if record.member else None,
    )


@router.post("/", response_model=BorrowRecordResponse, status_code=201, summary="Borrow a book")
async def borrow(
    request: BorrowRequest,
    svc: BorrowService = Depends(get_borrow_service),
):
    """
    Record a member borrowing a book.

    Business rules:
    - Book must have available copies
    - Member must be active
    - Member cannot borrow the same book twice simultaneously
    """
    try:
        record = await svc.borrow_book(
            book_id=request.book_id,
            member_id=request.member_id,
            borrow_days=request.borrow_days,
        )
        return _to_response(record)
    except BorrowError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/{record_id}/return", response_model=BorrowRecordResponse, summary="Return a book")
async def return_borrowed_book(
    record_id: int,
    svc: BorrowService = Depends(get_borrow_service),
):
    """Record the return of a borrowed book."""
    try:
        record = await svc.return_book(record_id)
        return _to_response(record)
    except BorrowError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/", response_model=BorrowRecordListResponse, summary="List borrow records")
async def list_borrow_records(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    member_id: int | None = Query(None, description="Filter by member ID"),
    book_id: int | None = Query(None, description="Filter by book ID"),
    status: str | None = Query(None, description="Filter by status (BORROWED, RETURNED, OVERDUE)"),
    svc: BorrowService = Depends(get_borrow_service),
):
    """List all borrow records with optional filters for member, book, and status."""
    records, total = await svc.get_borrow_records(
        page=page, size=size, member_id=member_id, book_id=book_id, status=status
    )
    return BorrowRecordListResponse(
        items=[_to_response(r) for r in records],
        total=total,
        page=page,
        size=size,
    )


@router.get("/overdue", response_model=BorrowRecordListResponse, summary="List overdue books")
async def list_overdue(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    svc: BorrowService = Depends(get_borrow_service),
):
    """List all books that are past their due date and have not been returned."""
    records, total = await svc.get_overdue_records(page=page, size=size)
    return BorrowRecordListResponse(
        items=[_to_response(r) for r in records],
        total=total,
        page=page,
        size=size,
    )


@router.get(
    "/member/{member_id}",
    response_model=list[BorrowRecordResponse],
    summary="Get books borrowed by a member",
)
async def member_borrowed_books(
    member_id: int,
    svc: BorrowService = Depends(get_borrow_service),
):
    """Get all currently borrowed (or overdue) books for a specific member."""
    try:
        records = await svc.get_member_borrowed_books(member_id)
        return [_to_response(r) for r in records]
    except BorrowError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
