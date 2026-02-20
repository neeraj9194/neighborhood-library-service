"""Stats router — library-wide aggregated metrics."""
from fastapi import APIRouter, Depends

from app.api.v1.dependencies import get_stats_service
from app.schemas.stats import StatsResponse
from app.services.stats import StatsService

router = APIRouter(prefix="/api/v1/stats", tags=["Stats"])


@router.get("/", response_model=StatsResponse, summary="Get library stats")
async def get_stats(svc: StatsService = Depends(get_stats_service)):
    """Return aggregated library statistics for the dashboard."""
    return await svc.get_stats()
