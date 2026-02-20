"""Integration tests for /api/v1/members endpoints."""

BASE = "/api/v1/members"


def _member_payload(**kwargs):
    data = {"name": "Jane Doe", "email": "jane@example.com"}
    data.update(kwargs)
    return data


# ── POST /members ─────────────────────────────────────────────────────────────

class TestCreateMember:
    async def test_returns_201_with_body(self, client):
        resp = await client.post(BASE + "/", json=_member_payload())
        assert resp.status_code == 201
        body = resp.json()
        assert isinstance(body["id"], int)
        assert body["name"] == "Jane Doe"
        assert body["is_active"] is True

    async def test_duplicate_email_returns_409(self, client):
        await client.post(BASE + "/", json=_member_payload())
        resp = await client.post(BASE + "/", json=_member_payload())
        assert resp.status_code == 409

    async def test_invalid_email_returns_422(self, client):
        resp = await client.post(BASE + "/", json=_member_payload(email="not-an-email"))
        assert resp.status_code == 422

    async def test_missing_name_returns_422(self, client):
        resp = await client.post(BASE + "/", json={"email": "ok@x.com"})
        assert resp.status_code == 422


# ── GET /members ──────────────────────────────────────────────────────────────

class TestListMembers:
    async def test_empty_list(self, client):
        resp = await client.get(BASE + "/")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    async def test_returns_created_members(self, client):
        await client.post(BASE + "/", json=_member_payload(email="a@x.com"))
        await client.post(BASE + "/", json=_member_payload(name="Bob", email="b@x.com"))
        resp = await client.get(BASE + "/")
        assert resp.json()["total"] == 2

    async def test_search_by_name(self, client):
        await client.post(BASE + "/", json=_member_payload(name="Alice", email="alice@x.com"))
        await client.post(BASE + "/", json=_member_payload(name="Bob", email="bob@x.com"))
        resp = await client.get(BASE + "/", params={"search": "alice"})
        assert resp.json()["total"] == 1

    async def test_filter_active(self, client):
        created = (await client.post(BASE + "/", json=_member_payload())).json()
        # deactivate the member
        await client.delete(f"{BASE}/{created['id']}")
        resp = await client.get(BASE + "/", params={"is_active": "false"})
        assert resp.json()["total"] == 1

    async def test_pagination_fields_present(self, client):
        for i in range(4):
            await client.post(BASE + "/", json=_member_payload(name=f"User{i}", email=f"u{i}@x.com"))
        resp = await client.get(BASE + "/", params={"page": 1, "size": 2})
        body = resp.json()
        assert body["total"] == 4
        assert len(body["items"]) == 2


# ── GET /members/{id} ─────────────────────────────────────────────────────────

class TestGetMember:
    async def test_returns_member_by_id(self, client):
        created = (await client.post(BASE + "/", json=_member_payload())).json()
        resp = await client.get(f"{BASE}/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_404_for_unknown_id(self, client):
        resp = await client.get(f"{BASE}/99999")
        assert resp.status_code == 404


# ── PATCH /members/{id} ───────────────────────────────────────────────────────

class TestUpdateMember:
    async def test_updates_name(self, client):
        created = (await client.post(BASE + "/", json=_member_payload())).json()
        resp = await client.patch(f"{BASE}/{created['id']}", json={"name": "Updated Name"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Name"

    async def test_updates_phone_and_address(self, client):
        created = (await client.post(BASE + "/", json=_member_payload())).json()
        resp = await client.patch(
            f"{BASE}/{created['id']}",
            json={"phone": "+1-555-0100", "address": "1 Test Ave"},
        )
        assert resp.json()["phone"] == "+1-555-0100"
        assert resp.json()["address"] == "1 Test Ave"

    async def test_404_for_unknown_id(self, client):
        resp = await client.patch(f"{BASE}/99999", json={"name": "Ghost"})
        assert resp.status_code == 404


# ── DELETE /members/{id} (deactivate) ────────────────────────────────────────

class TestDeactivateMember:
    async def test_deactivates_member(self, client):
        created = (await client.post(BASE + "/", json=_member_payload())).json()
        resp = await client.delete(f"{BASE}/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    async def test_404_for_unknown_id(self, client):
        resp = await client.delete(f"{BASE}/99999")
        assert resp.status_code == 404
