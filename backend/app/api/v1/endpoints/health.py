"""Health check endpoints for application and database connectivity monitoring."""

from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.health_service import HealthService
from app.schemas.health import (
    HealthCheckResponse,
    DatabaseHealthResponse,
    DetailedHealthResponse,
)

router = APIRouter(prefix="/health", tags=["Health Checks"])


@router.get(
    "",
    response_model=HealthCheckResponse,
    summary="Application Health Check",
    description="Returns operational status of the FastAPI application tier.",
)
def check_application_health(db: Session = Depends(get_db)) -> HealthCheckResponse:
    """Basic health check endpoint."""
    service = HealthService(db)
    return service.get_application_health()


@router.get(
    "/db",
    response_model=DatabaseHealthResponse,
    summary="Database Connectivity Check",
    description="Tests connectivity against the MySQL 8.4 Data Tier via SQLAlchemy.",
)
def check_database_health(
    response: Response,
    db: Session = Depends(get_db),
) -> DatabaseHealthResponse:
    """Verifies MySQL database connectivity and round-trip latency."""
    service = HealthService(db)
    db_health = service.get_database_health()
    if db_health.status != "connected":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return db_health


@router.get(
    "/detailed",
    response_model=DetailedHealthResponse,
    summary="Full System Health Check",
    description="Returns combined health diagnostics for both application and database tiers.",
)
def check_detailed_health(
    response: Response,
    db: Session = Depends(get_db),
) -> DetailedHealthResponse:
    """Comprehensive health check spanning all infrastructure tiers."""
    service = HealthService(db)
    detailed = service.get_detailed_health()
    if detailed.status != "healthy":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return detailed

