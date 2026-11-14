/**
 * Health and diagnostics API caller functions.
 */

import { apiClient } from './client';
import { HealthCheckResponse, DatabaseHealthResponse, DetailedHealthResponse } from '../types/health';

export const healthApi = {
  getAppHealth: (): Promise<HealthCheckResponse> => {
    return apiClient<HealthCheckResponse>('/health');
  },

  getDbHealth: (): Promise<DatabaseHealthResponse> => {
    return apiClient<DatabaseHealthResponse>('/health/db');
  },

  getDetailedHealth: (): Promise<DetailedHealthResponse> => {
    return apiClient<DetailedHealthResponse>('/health/detailed');
  },
};

