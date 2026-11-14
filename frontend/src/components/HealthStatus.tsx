import React from 'react';
import { DetailedHealthResponse } from '../types/health';
import { CheckCircle2, XCircle, Database, Server, RefreshCw } from 'lucide-react';

interface HealthStatusProps {
  data: DetailedHealthResponse | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
}

export const HealthStatus: React.FC<HealthStatusProps> = ({
  data,
  loading,
  error,
  onRefresh,
}) => {
  return (
    <div className="health-card">
      <div className="card-header">
        <div className="title-area">
          <h2>Three-Tier Architecture Health Status</h2>
          <p className="subtitle">Real-time status verified across Presentation, Application, and Data tiers</p>
        </div>
        <button
          className="refresh-btn"
          onClick={onRefresh}
          disabled={loading}
          aria-label="Refresh status"
        >
          <RefreshCw className={loading ? 'spin' : ''} size={18} />
          <span>{loading ? 'Verifying...' : 'Refresh Status'}</span>
        </button>
      </div>

      {error && (
        <div className="error-banner">
          <XCircle size={20} />
          <div>
            <strong>Tier Communication Error:</strong> {error}
          </div>
        </div>
      )}

      <div className="tiers-grid">
        {/* Tier 1: Presentation */}
        <div className="tier-box">
          <div className="tier-badge">Tier 1</div>
          <div className="tier-header">
            <span className="tier-icon">⚛️</span>
            <h3>Presentation Tier</h3>
          </div>
          <p className="tier-tech">React 18 + Vite + TypeScript</p>
          <div className="status-badge status-ok">
            <CheckCircle2 size={16} />
            <span>Operational (Client-side)</span>
          </div>
          <div className="details-list">
            <div className="detail-item">
              <span>Protocol:</span> <code>REST / JSON</code>
            </div>
            <div className="detail-item">
              <span>Port:</span> <code>5173</code>
            </div>
          </div>
        </div>

        {/* Tier 2: Application */}
        <div className="tier-box">
          <div className="tier-badge">Tier 2</div>
          <div className="tier-header">
            <Server size={22} className="tier-icon-lucide" />
            <h3>Application Tier</h3>
          </div>
          <p className="tier-tech">Python + FastAPI + Pydantic</p>
          <div className={`status-badge ${data?.status === 'healthy' ? 'status-ok' : error ? 'status-err' : 'status-pending'}`}>
            {data?.status === 'healthy' ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
            <span>{data ? `${data.status.toUpperCase()}` : 'Connecting...'}</span>
          </div>
          <div className="details-list">
            <div className="detail-item">
              <span>Service:</span> <strong>{data?.app || 'NexLead API'}</strong>
            </div>
            <div className="detail-item">
              <span>Environment:</span> <code>{data?.environment || 'unknown'}</code>
            </div>
            <div className="detail-item">
              <span>Endpoint:</span> <code>/api/v1/health</code>
            </div>
          </div>
        </div>

        {/* Tier 3: Data */}
        <div className="tier-box">
          <div className="tier-badge">Tier 3</div>
          <div className="tier-header">
            <Database size={22} className="tier-icon-lucide" />
            <h3>Data Tier</h3>
          </div>
          <p className="tier-tech">MySQL 8.4 via SQLAlchemy ORM</p>
          <div className={`status-badge ${data?.database?.status === 'connected' ? 'status-ok' : 'status-err'}`}>
            {data?.database?.status === 'connected' ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
            <span>{data?.database?.status === 'connected' ? 'CONNECTED' : 'DISCONNECTED'}</span>
          </div>
          <div className="details-list">
            <div className="detail-item">
              <span>Engine:</span> <strong>{data?.database?.database?.toUpperCase() || 'MYSQL'} {data?.database?.version || ''}</strong>
            </div>
            <div className="detail-item">
              <span>Database:</span> <code>{data?.database?.database_name || 'lead_intelligence'}</code>
            </div>
            <div className="detail-item">
              <span>Ping Latency:</span> <code>{data?.database?.latency_ms !== undefined ? `${data.database.latency_ms} ms` : 'N/A'}</code>
            </div>
          </div>
        </div>
      </div>

      {data?.timestamp && (
        <div className="card-footer">
          <span>Last Verified: {new Date(data.timestamp).toLocaleString()}</span>
          <span>Response Mode: Synchronous JSON API</span>
        </div>
      )}
    </div>
  );
};

