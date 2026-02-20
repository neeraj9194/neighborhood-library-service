"""Integration tests for /api/v1/books endpoints."""

BASE = "/api/v1/books"


def _book_payload(**kwargs):
    data = {"title": "Dune", "author": "Frank Herbert", "total_copies": 2}
    data.update(kwargs)
    return data


# ── POST /books ───────────────────────────────────────────────────────────────

class TestCreateBook:
    async def test_returns_201_with_body(self, client):
        resp = await client.post(BASE + "/", json=_book_payload())
        assert resp.status_code == 201
        body = resp.json()
        assert body["id"] is not None
        assert isinstance(body["id"], int)
        assert body["title"] == "Dune"
        assert body["available_copies"] == 2

    async def test_duplicate_isbn_returns_409(self, client):
        await client.post(BASE + "/", json=_book_payload(isbn="1234567890123"))
        resp = await client.post(BASE + "/", json=_book_payload(isbn="1234567890123"))
        assert resp.status_code == 409

    async def test_missing_required_field_returns_422(self, client):
        resp = await client.post(BASE + "/", json={"author": "No Title"})
        assert resp.status_code == 422


# ── GET /books ────────────────────────────────────────────────────────────────

class TestListBooks:
    async def test_empty_list(self, client):
        resp = await client.get(BASE + "/")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 0
        assert body["items"] == []

    async def test_returns_created_books(self, client):
        await client.post(BASE + "/", json=_book_payload(title="Book A"))
        await client.post(BASE + "/", json=_book_payload(title="Book B"))
        resp = await client.get(BASE + "/")
        assert resp.json()["total"] == 2

    async def test_search_query_filters_results(self, client):
        await client.post(BASE + "/", json=_book_payload(title="Dune"))
        await client.post(BASE + "/", json=_book_payload(title="Foundation"))
        resp = await client.get(BASE + "/", params={"search": "dune"})
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["title"] == "Dune"

    async def test_genre_filter(self, client):
        await client.post(BASE + "/", json=_book_payload(genre="Sci-Fi"))
        await client.post(BASE + "/", json=_book_payload(genre="Fantasy"))
        resp = await client.get(BASE + "/", params={"genre": "sci-fi"})
        assert resp.json()["total"] == 1

    async def test_pagination_fields_present(self, client):
        for i in range(3):
            await client.post(BASE + "/", json=_book_payload(title=f"Book {i}"))
        resp = await client.get(BASE + "/", params={"page": 1, "size": 2})
        body = resp.json()
        assert body["total"] == 3
        assert len(body["items"]) == 2
        assert body["page"] == 1
        assert body["size"] == 2


# ── GET /books/{id} ───────────────────────────────────────────────────────────

class TestGetBook:
    async def test_returns_book_by_id(self, client):
        created = (await client.post(BASE + "/", json=_book_payload())).json()
        resp = await client.get(f"{BASE}/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_404_for_unknown_id(self, client):
        resp = await client.get(f"{BASE}/99999")
        assert resp.status_code == 404


# ── PATCH /books/{id} ────────────────────────────────────────────────────────

class TestUpdateBook:
    async def test_updates_title(self, client):
        created = (await client.post(BASE + "/", json=_book_payload())).json()
        resp = await client.patch(f"{BASE}/{created['id']}", json={"title": "New Title"})
        assert resp.status_code == 200
        assert resp.json()["title"] == "New Title"

    async def test_partial_update_preserves_other_fields(self, client):
        created = (await client.post(BASE + "/", json=_book_payload())).json()
        await client.patch(f"{BASE}/{created['id']}", json={"title": "Changed"})
        resp = await client.get(f"{BASE}/{created['id']}")
        assert resp.json()["author"] == "Frank Herbert"

    async def test_404_for_unknown_id(self, client):
        resp = await client.patch(f"{BASE}/99999", json={"title": "X"})
        assert resp.status_code == 404


# ── DELETE /books/{id} ───────────────────────────────────────────────────────

class TestDeleteBook:
    async def test_deletes_and_returns_204(self, client):
        created = (await client.post(BASE + "/", json=_book_payload())).json()
        resp = await client.delete(f"{BASE}/{created['id']}")
        assert resp.status_code == 204

    async def test_deleted_book_is_not_found(self, client):
        created = (await client.post(BASE + "/", json=_book_payload())).json()
        await client.delete(f"{BASE}/{created['id']}")
        resp = await client.get(f"{BASE}/{created['id']}")
        assert resp.status_code == 404

    async def test_404_for_unknown_id(self, client):
        resp = await client.delete(f"{BASE}/99999")
        assert resp.status_code == 404
