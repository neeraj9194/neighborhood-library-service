from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import RegisterTortoise

from app.core.config import get_settings
from app.database import TORTOISE_ORM
from app.api.v1.routes.books import router as books_router
from app.api.v1.routes.members import router as members_router
from app.api.v1.routes.borrow import router as borrow_router
from app.api.v1.routes.stats import router as stats_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage Tortoise ORM lifecycle — connect on startup, disconnect on shutdown."""
    async with RegisterTortoise(
        app,
        config=TORTOISE_ORM,
        generate_schemas=True,
        add_exception_handlers=True,
    ):
        yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## Neighborhood Library Service API

A REST API for managing a neighborhood library's books, members, and lending operations.

### Features
- **Books** – Create, update, search, and delete book records
- **Members** – Register, update, search, and deactivate library members
- **Borrowing** – Borrow books, return books, track overdue items
- **Queries** – Search by member, status, view overdue books

### Business Rules
- Members must be **active** to borrow books
- Books must have **available copies** to be borrowed
- A member **cannot borrow the same book twice** simultaneously
- Default borrow period is **14 days**
- Overdue books are automatically flagged
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS - allow all origins for development (restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(books_router)
app.include_router(members_router)
app.include_router(borrow_router)
app.include_router(stats_router)


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "healthy",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check."""
    return {"status": "ok"}
