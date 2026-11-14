/**
 * TypeScript interfaces matching backend Pydantic schemas.
 */

export interface HealthCheckResponse {
  status: string;
  app: string;
  version: string;
  environment: string;
  timestamp: string;
}

export interface DatabaseHealthResponse {
  status: 'connected' | 'disconnected' | string;
  database: string;
  version?: string | null;
  latency_ms?: number | null;
  database_name?: string | null;
  message?: string | null;
}

export interface DetailedHealthResponse {
  status: string;
  app: string;
  environment: string;
  database: DatabaseHealthResponse;
  timestamp: string;
}

