"""
Shared fixtures for unit and integration tests.

Both use an in-memory SQLite database via Tortoise's test helpers so the tests
run completely independently of any external Postgres instance.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from tortoise import Tortoise

# Tortoise config pointing at SQLite in-memory for testing
TEST_TORTOISE_CONFIG = {
    "connections": {
        "default": "sqlite://:memory:",
    },
    "apps": {
        "models": {
            "models": ["app.models"],
            "default_connection": "default",
        },
    },
}


@pytest_asyncio.fixture(autouse=False)
async def init_db():
    """
    Initialise an isolated in-memory SQLite DB for each test.
    Tables are created before the test and torn down afterwards.
    """
    await Tortoise.init(config=TEST_TORTOISE_CONFIG)
    await Tortoise.generate_schemas(safe=True)
    yield
    await Tortoise.close_connections()


@pytest_asyncio.fixture
async def client(init_db):
    """
    Async HTTP client wired directly to the FastAPI app (no real network).
    The in-memory DB is already initialised by the `init_db` fixture.
    We patch Tortoise inside the app so it re-uses the same in-memory
    connection rather than trying to connect to Postgres.
    """
    # Import app *after* Tortoise is already initialised so the app's
    # lifespan (RegisterTortoise) is bypassed.
    from app.main import app

    # Override the lifespan so it doesn't re-initialise Tortoise
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def _noop_lifespan(app):
        yield

    app.router.lifespan_context = _noop_lifespan

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
