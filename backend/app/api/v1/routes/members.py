"""Members router — HTTP layer only. Delegates all logic to MemberService."""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from tortoise.exceptions import IntegrityError

from app.api.v1.dependencies import get_member_service
from app.schemas.member import MemberCreate, MemberUpdate, MemberResponse, MemberListResponse
from app.services.member import MemberService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/members", tags=["Members"])


@router.post("/", response_model=MemberResponse, status_code=201, summary="Register a new member")
async def create_member(
    data: MemberCreate,
    svc: MemberService = Depends(get_member_service),
):
    """Register a new library member."""
    try:
        member = await svc.create_member(data)
        return MemberResponse.model_validate(member, from_attributes=True)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="A member with this email already exists")
    except Exception:
        logger.exception("Unexpected error creating member")
        raise HTTPException(status_code=500, detail="Failed to create member")


@router.get("/", response_model=MemberListResponse, summary="List all members")
async def list_members(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Search by name or email"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    svc: MemberService = Depends(get_member_service),
):
    """List all library members with optional search and active-status filter."""
    members, total = await svc.get_members(
        page=page, size=size, search=search, is_active=is_active
    )
    return MemberListResponse(
        items=[MemberResponse.model_validate(m, from_attributes=True) for m in members],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{member_id}", response_model=MemberResponse, summary="Get a member by ID")
async def get_member(
    member_id: int,
    svc: MemberService = Depends(get_member_service),
):
    """Get detailed information about a specific member."""
    member = await svc.get_member(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return MemberResponse.model_validate(member, from_attributes=True)


@router.patch("/{member_id}", response_model=MemberResponse, summary="Update a member")
async def update_member(
    member_id: int,
    data: MemberUpdate,
    svc: MemberService = Depends(get_member_service),
):
    """Update an existing member's details. Only provided fields will be updated."""
    member = await svc.update_member(member_id, data)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return MemberResponse.model_validate(member, from_attributes=True)


@router.delete("/{member_id}", response_model=MemberResponse, summary="Deactivate a member")
async def deactivate_member(
    member_id: int,
    svc: MemberService = Depends(get_member_service),
):
    """Soft-delete a member by deactivating their account."""
    member = await svc.deactivate_member(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return MemberResponse.model_validate(member, from_attributes=True)
