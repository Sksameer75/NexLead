"""Service managing health evaluation and diagnostic orchestration."""

import time
from sqlalchemy.orm import Session
from app.core.config import settings
from app.repositories.health_repository import HealthRepository
from app.schemas.health import (
    HealthCheckResponse,
    DatabaseHealthResponse,
    DetailedHealthResponse,
)


class HealthService:
    """Business logic for checking application and database health."""

    def __init__(self, db: Session):
        self.repository = HealthRepository(db)

    def get_application_health(self) -> HealthCheckResponse:
        """Returns the core operational status of the application tier."""
        return HealthCheckResponse(
            status="healthy",
            app=settings.PROJECT_NAME,
            version=settings.VERSION,
            environment=settings.ENVIRONMENT,
        )

    def get_database_health(self) -> DatabaseHealthResponse:
        """
        Executes a database connectivity check through the repository,
        measuring round-trip latency and capturing operational diagnostics.
        """
        start_time = time.perf_counter()
        try:
            db_info = self.repository.ping()
            latency = (time.perf_counter() - start_time) * 1000.0  # ms

            if db_info.get("ping") == 1:
                return DatabaseHealthResponse(
                    status="connected",
                    database="mysql",
                    version=db_info.get("version"),
                    latency_ms=round(latency, 2),
                    database_name=db_info.get("database_name"),
                    message="Database connection established successfully",
                )
            else:
                return DatabaseHealthResponse(
                    status="disconnected",
                    database="mysql",
                    latency_ms=round(latency, 2),
                    message="Ping query returned invalid response",
                )
        except Exception as exc:
            latency = (time.perf_counter() - start_time) * 1000.0
            return DatabaseHealthResponse(
                status="disconnected",
                database="mysql",
                latency_ms=round(latency, 2),
                message=f"Database connection error: {str(exc)}",
            )

    def get_detailed_health(self) -> DetailedHealthResponse:
        """Combines application tier and data tier operational statuses."""
        db_health = self.get_database_health()
        overall_status = "healthy" if db_health.status == "connected" else "degraded"

        return DetailedHealthResponse(
            status=overall_status,
            app=settings.PROJECT_NAME,
            environment=settings.ENVIRONMENT,
            database=db_health,
        )

