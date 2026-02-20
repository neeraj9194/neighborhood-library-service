"""Member service — business logic that sits between routes and the repository."""
from app.models.member import Member
from app.repositories.member import MemberRepository
from app.schemas.member import MemberCreate, MemberUpdate


class MemberService:
    def __init__(self, repo: MemberRepository) -> None:
        self._repo = repo

    async def create_member(self, data: MemberCreate) -> Member:
        return await self._repo.create(data)

    async def get_member(self, member_id: int) -> Member | None:
        return await self._repo.get_by_id(member_id)

    async def get_members(
        self,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[Member], int]:
        return await self._repo.get_all(
            page=page, size=size, search=search, is_active=is_active
        )

    async def update_member(self, member_id: int, data: MemberUpdate) -> Member | None:
        member = await self._repo.get_by_id(member_id)
        if not member:
            return None
        return await self._repo.update(member, data.model_dump(exclude_unset=True))

    async def deactivate_member(self, member_id: int) -> Member | None:
        """Soft-delete: set is_active=False rather than removing the record."""
        member = await self._repo.get_by_id(member_id)
        if not member:
            return None
        return await self._repo.update(member, {"is_active": False})
