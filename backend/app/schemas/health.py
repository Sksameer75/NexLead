"""Pydantic models for health check requests and responses."""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


def get_utc_now() -> datetime:
    """Helper to return current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


class HealthCheckResponse(BaseModel):
    """Basic application health response schema."""

    status: str = Field(..., description="Application operational status, e.g. 'healthy'")
    app: str = Field(..., description="Application name")
    version: str = Field(..., description="Application semantic version")
    environment: str = Field(..., description="Active runtime environment")
    timestamp: datetime = Field(default_factory=get_utc_now, description="UTC response timestamp")


class DatabaseHealthResponse(BaseModel):
    """Database connectivity health check response schema."""

    status: str = Field(..., description="Connection status: 'connected' or 'disconnected'")
    database: str = Field(default="mysql", description="Database engine type")
    version: Optional[str] = Field(None, description="Reported database engine version")
    latency_ms: Optional[float] = Field(None, description="Round-trip query latency in milliseconds")
    database_name: Optional[str] = Field(None, description="Connected schema name")
    message: Optional[str] = Field(None, description="Status detail or error message if disconnected")


class DetailedHealthResponse(BaseModel):
    """Comprehensive health status including application and database tier."""

    status: str = Field(..., description="Overall system health status")
    app: str = Field(..., description="Application name")
    environment: str = Field(..., description="Active runtime environment")
    database: DatabaseHealthResponse = Field(..., description="Database connectivity status")
    timestamp: datetime = Field(default_factory=get_utc_now, description="UTC response timestamp")
