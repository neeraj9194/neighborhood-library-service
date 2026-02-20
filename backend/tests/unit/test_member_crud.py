"""Unit tests for MemberService (member.py service + repository)."""
import pytest
from app.repositories.member import MemberRepository
from app.services.member import MemberService
from app.schemas.member import MemberCreate, MemberUpdate


def _svc() -> MemberService:
    return MemberService(repo=MemberRepository())


def _member_create(**kwargs) -> MemberCreate:
    defaults = dict(name="Jane Doe", email="jane@example.com")
    defaults.update(kwargs)
    return MemberCreate(**defaults)


# ── create_member ────────────────────────────────────────────────────────────

class TestCreateMember:
    async def test_creates_and_returns_member(self, init_db):
        member = await _svc().create_member(_member_create())
        assert member.id is not None
        assert member.name == "Jane Doe"
        assert member.email == "jane@example.com"

    async def test_is_active_by_default(self, init_db):
        member = await _svc().create_member(_member_create())
        assert member.is_active is True

    async def test_optional_fields_default_to_none(self, init_db):
        member = await _svc().create_member(_member_create())
        assert member.phone is None
        assert member.address is None


# ── get_member ───────────────────────────────────────────────────────────────

class TestGetMember:
    async def test_returns_existing_member(self, init_db):
        svc = _svc()
        created = await svc.create_member(_member_create())
        fetched = await svc.get_member(created.id)
        assert fetched is not None
        assert fetched.id == created.id

    async def test_returns_none_for_missing_id(self, init_db):
        result = await _svc().get_member(99999)
        assert result is None


# ── get_members ──────────────────────────────────────────────────────────────

class TestGetMembers:
    async def test_returns_all_members(self, init_db):
        svc = _svc()
        await svc.create_member(_member_create(email="a@x.com"))
        await svc.create_member(_member_create(name="Bob", email="b@x.com"))
        members, total = await svc.get_members()
        assert total == 2

    async def test_search_by_name(self, init_db):
        svc = _svc()
        await svc.create_member(_member_create(name="Alice", email="alice@x.com"))
        await svc.create_member(_member_create(name="Bob", email="bob@x.com"))
        members, total = await svc.get_members(search="alice")
        assert total == 1
        assert members[0].name == "Alice"

    async def test_search_by_email(self, init_db):
        svc = _svc()
        await svc.create_member(_member_create(email="unique@domain.com"))
        await svc.create_member(_member_create(name="Other", email="other@x.com"))
        members, total = await svc.get_members(search="unique@domain")
        assert total == 1

    async def test_filter_active_members(self, init_db):
        svc = _svc()
        m = await svc.create_member(_member_create(email="active@x.com"))
        inactive = await svc.create_member(_member_create(name="Inactive", email="inactive@x.com"))
        await svc.deactivate_member(inactive.id)
        members, total = await svc.get_members(is_active=True)
        assert total == 1
        assert members[0].id == m.id

    async def test_filter_inactive_members(self, init_db):
        svc = _svc()
        await svc.create_member(_member_create(email="active@x.com"))
        inactive = await svc.create_member(_member_create(name="Inactive", email="inactive@x.com"))
        await svc.deactivate_member(inactive.id)
        members, total = await svc.get_members(is_active=False)
        assert total == 1
        assert members[0].id == inactive.id

    async def test_pagination(self, init_db):
        svc = _svc()
        for i in range(5):
            await svc.create_member(_member_create(name=f"User{i}", email=f"u{i}@x.com"))
        members, total = await svc.get_members(page=2, size=2)
        assert total == 5
        assert len(members) == 2


# ── update_member ─────────────────────────────────────────────────────────────

class TestUpdateMember:
    async def test_updates_name(self, init_db):
        svc = _svc()
        member = await svc.create_member(_member_create())
        updated = await svc.update_member(member.id, MemberUpdate(name="New Name"))
        assert updated.name == "New Name"

    async def test_updates_phone_and_address(self, init_db):
        svc = _svc()
        member = await svc.create_member(_member_create())
        updated = await svc.update_member(
            member.id, MemberUpdate(phone="+1-555-0199", address="99 Test St")
        )
        assert updated.phone == "+1-555-0199"
        assert updated.address == "99 Test St"

    async def test_returns_none_for_missing_member(self, init_db):
        result = await _svc().update_member(99999, MemberUpdate(name="Ghost"))
        assert result is None


# ── deactivate_member ─────────────────────────────────────────────────────────

class TestDeactivateMember:
    async def test_sets_is_active_false(self, init_db):
        svc = _svc()
        member = await svc.create_member(_member_create())
        deactivated = await svc.deactivate_member(member.id)
        assert deactivated.is_active is False

    async def test_returns_none_for_missing_member(self, init_db):
        result = await _svc().deactivate_member(99999)
        assert result is None
