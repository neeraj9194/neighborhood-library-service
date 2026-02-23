"""Integration tests for /api/v1/borrow endpoints."""

BORROW_BASE = "/api/v1/borrow"
BOOKS_BASE = "/api/v1/books"
MEMBERS_BASE = "/api/v1/members"


async def _create_book(client, total_copies=3, title="Test Book"):
    resp = await client.post(
        BOOKS_BASE + "/",
        json={"title": title, "author": "Author", "total_copies": total_copies},
    )
    return resp.json()


async def _create_member(client, email="member@example.com", name="Test Member"):
    resp = await client.post(
        MEMBERS_BASE + "/",
        json={"name": name, "email": email},
    )
    return resp.json()


# ── POST /borrow (borrow a book) ──────────────────────────────────────────────

class TestBorrowBook:
    async def test_creates_borrow_record(self, client):
        book = await _create_book(client)
        member = await _create_member(client)
        resp = await client.post(
            BORROW_BASE + "/",
            json={"book_id": book["id"], "member_id": member["id"]},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert isinstance(body["id"], int)
        assert body["book_id"] == book["id"]
        assert body["member_id"] == member["id"]
        assert body["status"] == "BORROWED"
        assert body["returned_at"] is None

    async def test_includes_nested_book_and_member_info(self, client):
        book = await _create_book(client)
        member = await _create_member(client)
        resp = await client.post(
            BORROW_BASE + "/",
            json={"book_id": book["id"], "member_id": member["id"]},
        )
        body = resp.json()
        assert body["book_title"] == "Test Book"
        assert body["member_name"] == "Test Member"

    async def test_custom_borrow_days(self, client):
        book = await _create_book(client)
        member = await _create_member(client)
        resp = await client.post(
            BORROW_BASE + "/",
            json={"book_id": book["id"], "member_id": member["id"], "borrow_days": 7},
        )
        assert resp.status_code == 201

    async def test_book_not_found_returns_404(self, client):
        member = await _create_member(client)
        resp = await client.post(
            BORROW_BASE + "/",
            json={"book_id": 99999, "member_id": member["id"]},
        )
        assert resp.status_code == 404

    async def test_member_not_found_returns_404(self, client):
        book = await _create_book(client)
        resp = await client.post(
            BORROW_BASE + "/",
            json={"book_id": book["id"], "member_id": 99999},
        )
        assert resp.status_code == 404

    async def test_no_copies_available_returns_400(self, client):
        book = await _create_book(client, total_copies=1)
        m1 = await _create_member(client, email="m1@x.com")
        m2 = await _create_member(client, email="m2@x.com", name="Member 2")
        await client.post(
            BORROW_BASE + "/",
            json={"book_id": book["id"], "member_id": m1["id"]},
        )
        resp = await client.post(
            BORROW_BASE + "/",
            json={"book_id": book["id"], "member_id": m2["id"]},
        )
        assert resp.status_code == 400

    async def test_double_borrow_same_book_returns_400(self, client):
        book = await _create_book(client, total_copies=5)
        member = await _create_member(client)
        await client.post(
            BORROW_BASE + "/",
            json={"book_id": book["id"], "member_id": member["id"]},
        )
        resp = await client.post(
            BORROW_BASE + "/",
            json={"book_id": book["id"], "member_id": member["id"]},
        )
        assert resp.status_code == 400

    async def test_inactive_member_returns_400(self, client):
        book = await _create_book(client)
        member = await _create_member(client)
        await client.delete(f"{MEMBERS_BASE}/{member['id']}")  # deactivate
        resp = await client.post(
            BORROW_BASE + "/",
            json={"book_id": book["id"], "member_id": member["id"]},
        )
        assert resp.status_code == 400


    async def test_negative_book_id_returns_422(self, client):
        member = await _create_member(client, email="neg@x.com")
        resp = await client.post(
            BORROW_BASE + "/",
            json={"book_id": -1, "member_id": member["id"]},
        )
        assert resp.status_code == 422

    async def test_zero_member_id_returns_422(self, client):
        book = await _create_book(client)
        resp = await client.post(
            BORROW_BASE + "/",
            json={"book_id": book["id"], "member_id": 0},
        )
        assert resp.status_code == 422


# ── POST /borrow/{id}/return ──────────────────────────────────────────────────

class TestReturnBook:
    async def test_returns_book_successfully(self, client):
        book = await _create_book(client)
        member = await _create_member(client)
        record = (
            await client.post(
                BORROW_BASE + "/",
                json={"book_id": book["id"], "member_id": member["id"]},
            )
        ).json()
        resp = await client.post(f"{BORROW_BASE}/{record['id']}/return")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "RETURNED"
        assert body["returned_at"] is not None

    async def test_record_not_found_returns_404(self, client):
        resp = await client.post(f"{BORROW_BASE}/99999/return")
        assert resp.status_code == 404

    async def test_already_returned_returns_400(self, client):
        book = await _create_book(client)
        member = await _create_member(client)
        record = (
            await client.post(
                BORROW_BASE + "/",
                json={"book_id": book["id"], "member_id": member["id"]},
            )
        ).json()
        await client.post(f"{BORROW_BASE}/{record['id']}/return")
        resp = await client.post(f"{BORROW_BASE}/{record['id']}/return")
        assert resp.status_code == 400


# ── GET /borrow ───────────────────────────────────────────────────────────────

class TestListBorrowRecords:
    async def test_empty_list(self, client):
        resp = await client.get(BORROW_BASE + "/")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    async def test_returns_all_records(self, client):
        book = await _create_book(client, total_copies=5)
        m1 = await _create_member(client, email="m1@x.com")
        m2 = await _create_member(client, email="m2@x.com", name="M2")
        await client.post(BORROW_BASE + "/", json={"book_id": book["id"], "member_id": m1["id"]})
        await client.post(BORROW_BASE + "/", json={"book_id": book["id"], "member_id": m2["id"]})
        resp = await client.get(BORROW_BASE + "/")
        assert resp.json()["total"] == 2

    async def test_filter_by_member_id(self, client):
        book = await _create_book(client, total_copies=5)
        m1 = await _create_member(client, email="m1@x.com")
        m2 = await _create_member(client, email="m2@x.com", name="M2")
        await client.post(BORROW_BASE + "/", json={"book_id": book["id"], "member_id": m1["id"]})
        await client.post(BORROW_BASE + "/", json={"book_id": book["id"], "member_id": m2["id"]})
        resp = await client.get(BORROW_BASE + "/", params={"member_id": m1["id"]})
        assert resp.json()["total"] == 1

    async def test_filter_by_book_id(self, client):
        b1 = await _create_book(client, title="Book A")
        b2 = await _create_book(client, title="Book B")
        m = await _create_member(client)
        await client.post(BORROW_BASE + "/", json={"book_id": b1["id"], "member_id": m["id"]})
        resp = await client.get(BORROW_BASE + "/", params={"book_id": b2["id"]})
        assert resp.json()["total"] == 0

    async def test_filter_by_status(self, client):
        book = await _create_book(client, total_copies=5)
        m1 = await _create_member(client, email="m1@x.com")
        m2 = await _create_member(client, email="m2@x.com", name="M2")
        r1 = (await client.post(BORROW_BASE + "/", json={"book_id": book["id"], "member_id": m1["id"]})).json()
        await client.post(BORROW_BASE + "/", json={"book_id": book["id"], "member_id": m2["id"]})
        await client.post(f"{BORROW_BASE}/{r1['id']}/return")
        resp = await client.get(BORROW_BASE + "/", params={"status": "RETURNED"})
        assert resp.json()["total"] == 1


# ── GET /borrow/overdue ───────────────────────────────────────────────────────

class TestOverdueRecords:
    async def test_returns_empty_when_no_overdue(self, client):
        resp = await client.get(BORROW_BASE + "/overdue")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0


# ── GET /borrow/member/{id} ───────────────────────────────────────────────────

class TestMemberBorrowedBooks:
    async def test_returns_active_borrows_for_member(self, client):
        book = await _create_book(client)
        member = await _create_member(client)
        await client.post(BORROW_BASE + "/", json={"book_id": book["id"], "member_id": member["id"]})
        resp = await client.get(f"{BORROW_BASE}/member/{member['id']}")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_excludes_returned_books(self, client):
        book = await _create_book(client)
        member = await _create_member(client)
        record = (
            await client.post(BORROW_BASE + "/", json={"book_id": book["id"], "member_id": member["id"]})
        ).json()
        await client.post(f"{BORROW_BASE}/{record['id']}/return")
        resp = await client.get(f"{BORROW_BASE}/member/{member['id']}")
        assert resp.json() == []

    async def test_member_not_found_returns_404(self, client):
        resp = await client.get(f"{BORROW_BASE}/member/99999")
        assert resp.status_code == 404
