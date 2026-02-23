"""Member service — business logic that sits between routes and the repository."""
import logging

from app.models.member import Member
from app.repositories.member import MemberRepository
from app.schemas.member import MemberCreate, MemberUpdate

logger = logging.getLogger(__name__)


class MemberService:
    def __init__(self, repo: MemberRepository) -> None:
        self._repo = repo

    async def create_member(self, data: MemberCreate) -> Member:
        logger.debug(
            "Creating member: name='%s', email='%s', phone=%s",
            data.name, data.email, data.phone,
        )
        member = await self._repo.create(data)
        logger.info(
            "Member created: id=%s, name='%s', email='%s'",
            member.id, member.name, member.email,
        )
        return member

    async def get_member(self, member_id: int) -> Member | None:
        logger.debug("Getting member: id=%s", member_id)
        member = await self._repo.get_by_id(member_id)
        if member:
            logger.debug("Member found: id=%s, name='%s', is_active=%s", member.id, member.name, member.is_active)
        else:
            logger.debug("Member not found: id=%s", member_id)
        return member

    async def get_members(
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
        members, total = await self._repo.get_all(
            page=page, size=size, search=search, is_active=is_active
        )
        logger.info("Members listed: total=%d, returned=%d", total, len(members))
        return members, total

    async def update_member(self, member_id: int, data: MemberUpdate) -> Member | None:
        update_fields = data.model_dump(exclude_unset=True)
        logger.info("Update requested: member_id=%s, fields=%s", member_id, update_fields)
        member = await self._repo.get_by_id(member_id)
        if not member:
            logger.debug("Update skipped: member_id=%s not found", member_id)
            return None
        result = await self._repo.update(member, update_fields)
        logger.info(
            "Member updated: id=%s, fields=%s",
            member_id, list(update_fields.keys()),
        )
        return result

    async def deactivate_member(self, member_id: int) -> Member | None:
        """Soft-delete: set is_active=False rather than removing the record."""
        logger.info("Deactivation requested: member_id=%s", member_id)
        member = await self._repo.get_by_id(member_id)
        if not member:
            logger.debug("Deactivation skipped: member_id=%s not found", member_id)
            return None
        logger.debug(
            "Deactivating member: id=%s, name='%s', current_is_active=%s",
            member.id, member.name, member.is_active,
        )
        result = await self._repo.update(member, {"is_active": False})
        logger.info("Member deactivated: id=%s, name='%s'", member_id, member.name)
        return result
