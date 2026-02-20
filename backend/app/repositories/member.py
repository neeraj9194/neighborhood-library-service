"""Member repository — pure database access, no business logic."""
from tortoise.expressions import Q

from app.models.member import Member
from app.schemas.member import MemberCreate, MemberUpdate


class MemberRepository:
    async def create(self, data: MemberCreate) -> Member:
        return await Member.create(**data.model_dump())

    async def get_by_id(self, member_id: int) -> Member | None:
        return await Member.get_or_none(id=member_id)

    async def get_all(
        self,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[Member], int]:
        qs = Member.all()
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(email__icontains=search))
        if is_active is not None:
            qs = qs.filter(is_active=is_active)
        total = await qs.count()
        members = await qs.offset((page - 1) * size).limit(size)
        return members, total

    async def update(self, member: Member, data: dict) -> Member:
        await member.update_from_dict(data).save()
        return member

    async def delete(self, member_id: int) -> bool:
        deleted = await Member.filter(id=member_id).delete()
        return deleted > 0
