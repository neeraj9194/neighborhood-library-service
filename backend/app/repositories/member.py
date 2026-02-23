"""Member repository — pure database access, no business logic."""
import logging

from tortoise.expressions import Q

from app.models.member import Member
from app.schemas.member import MemberCreate, MemberUpdate

logger = logging.getLogger(__name__)


class MemberRepository:
    async def create(self, data: MemberCreate) -> Member:
        logger.debug("Inserting member: name='%s', email='%s'", data.name, data.email)
        member = await Member.create(**data.model_dump())
        logger.debug("Inserted member: id=%s", member.id)
        return member

    async def get_by_id(self, member_id: int) -> Member | None:
        logger.debug("Fetching member: id=%s", member_id)
        member = await Member.get_or_none(id=member_id)
        logger.debug("Fetch result: id=%s found=%s", member_id, member is not None)
        return member

    async def get_all(
        self,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[Member], int]:
        logger.debug(
            "Listing members: page=%d, size=%d, search=%s, is_active=%s",
            page, size, search, is_active,
        )
        qs = Member.all()
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(email__icontains=search))
        if is_active is not None:
            qs = qs.filter(is_active=is_active)
        total = await qs.count()
        members = await qs.offset((page - 1) * size).limit(size)
        logger.debug("Listed members: total=%d, returned=%d", total, len(members))
        return members, total

    async def update(self, member: Member, data: dict) -> Member:
        logger.debug("Updating member: id=%s, fields=%s", member.id, data)
        await member.update_from_dict(data).save()
        logger.debug("Updated member: id=%s", member.id)
        return member

    async def delete(self, member_id: int) -> bool:
        logger.debug("Deleting member: id=%s", member_id)
        deleted = await Member.filter(id=member_id).delete()
        logger.debug("Delete result: id=%s, rows_deleted=%d", member_id, deleted)
        return deleted > 0
