"""Main FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.router import api_v1_router
from app import crm
from app import crm_extensions
from app import crm_campaigns
from app import crm_dedupe
from app.core.database import Base, engine
from app.schemas.health import HealthCheckResponse

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="NexLead â€” Professional Lead Intelligence and Sales Operations Platform API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None,
    docs_url=f"{settings.API_V1_STR}/docs" if settings.DEBUG else None,
    redoc_url=f"{settings.API_V1_STR}/redoc" if settings.DEBUG else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix=settings.API_V1_STR)
app.include_router(crm_extensions.router, prefix=settings.API_V1_STR)
app.include_router(crm_campaigns.router, prefix=settings.API_V1_STR)
app.include_router(crm_dedupe.router, prefix=settings.API_V1_STR)
app.include_router(crm.router, prefix=settings.API_V1_STR)


@app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
def root_health():
    return HealthCheckResponse(
        status="healthy",
        app=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
    )


@app.on_event("startup")
def initialize_database_tables():
    """Create missing tables without dropping existing tables or records."""
    Base.metadata.create_all(bind=engine)



