"""Repository for database connectivity and diagnostic queries."""

from typing import Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session


class HealthRepository:
    """Encapsulates data access queries for infrastructure and health checks."""

    def __init__(self, db: Session):
        self.db = db

    def ping(self) -> Dict[str, Any]:
        """
        Executes diagnostic queries to verify database connectivity and fetch metadata.
        Returns database version and active database name.
        """
        result = self.db.execute(text("SELECT 1 AS ping, VERSION() AS version, DATABASE() AS db_name")).fetchone()
        if result:
            return {
                "ping": result.ping,
                "version": result.version,
                "database_name": result.db_name,
            }
        return {"ping": 0, "version": None, "database_name": None}

