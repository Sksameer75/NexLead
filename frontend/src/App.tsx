
import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Activity,
  AlertCircle,
  ArrowUpRight,
  BarChart3,
  Bell,
  Building2,
  ChevronDown,
  CircleDollarSign,
  ClipboardList,
  Clock3,
  Filter,
  LayoutDashboard,
  Menu,
  RefreshCw,
  Search,
  Target,
  Users,
  X,
  Zap,
} from 'lucide-react';
import './App.css';

const API = 'http://127.0.0.1:8000/api/v1';

type RecordData = Record<string, unknown>;

type DashboardData = {
  summary: {
    total_leads: number;
    hot_leads: number;
    warm_leads: number;
    cold_leads: number;
    opportunities: number;
    won_opportunities: number;
    conversion_rate: number;
    pipeline_value: number;
    pending_tasks: number;
    overdue_tasks: number;
    average_lead_score: number;
  };
  opportunity_stages: Array<{ stage: string; count: number }>;
  lead_sources: Array<{ source: string; count: number }>;
};

const emptyDashboard: DashboardData = {
  summary: {
    total_leads: 0,
    hot_leads: 0,
    warm_leads: 0,
    cold_leads: 0,
    opportunities: 0,
    won_opportunities: 0,
    conversion_rate: 0,
    pipeline_value: 0,
    pending_tasks: 0,
    overdue_tasks: 0,
    average_lead_score: 0,
  },
  opportunity_stages: [],
  lead_sources: [],
};

function asRecord(value: unknown): RecordData {
  return value && typeof value === 'object'
    ? (value as RecordData)
    : {};
}

function read(
  object: RecordData,
  ...keys: string[]
): unknown {
  for (const key of keys) {
    if (object[key] !== undefined && object[key] !== null) {
      return object[key];
    }
  }
  return undefined;
}

function display(value: unknown, fallback = 'â€”'): string {
  if (value === undefined || value === null || value === '') {
    return fallback;
  }
  return String(value);
}

function numeric(value: unknown): number {
  const result = Number(value);
  return Number.isFinite(result) ? result : 0;
}

function money(value: unknown): string {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(numeric(value));
}

function normalizeList(value: unknown): RecordData[] {
  if (Array.isArray(value)) {
    return value.map(asRecord);
  }

  const record = asRecord(value);

  for (const key of ['items', 'results', 'data', 'leads', 'tasks', 'opportunities']) {
    if (Array.isArray(record[key])) {
      return (record[key] as unknown[]).map(asRecord);
    }
  }

  return [];
}

function getLeadName(lead: RecordData): string {
  const direct = read(lead, 'name', 'full_name', 'fullName');
  if (direct) return String(direct);

  const first = display(read(lead, 'first_name', 'firstName'), '');
  const last = display(read(lead, 'last_name', 'lastName'), '');
  return `${first} ${last}`.trim() || 'Unnamed lead';
}

function getStatusClass(status: string): string {
  const normalized = status.toLowerCase();

  if (['hot', 'won', 'completed', 'qualified', 'active'].includes(normalized)) {
    return 'status-pill status-success';
  }

  if (['warm', 'proposal', 'negotiation', 'pending', 'in progress'].includes(normalized)) {
    return 'status-pill status-warning';
  }

  if (['cold', 'lost', 'overdue', 'rejected'].includes(normalized)) {
    return 'status-pill status-danger';
  }

  return 'status-pill';
}

function App() {
  const [activePage, setActivePage] = useState('Dashboard');
  const [dashboard, setDashboard] = useState<DashboardData>(emptyDashboard);
  const [leads, setLeads] = useState<RecordData[]>([]);
  const [tasks, setTasks] = useState<RecordData[]>([]);
  const [opportunities, setOpportunities] = useState<RecordData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [lastUpdated, setLastUpdated] = useState('');

  const fetchJson = useCallback(async (path: string) => {
    const response = await fetch(`${API}${path}`);

    if (!response.ok) {
      throw new Error(`${path} returned HTTP ${response.status}`);
    }

    return response.json() as Promise<unknown>;
  }, []);

  const loadApplication = useCallback(async () => {
    setLoading(true);
    setError('');

    const results = await Promise.allSettled([
      fetchJson('/dashboard'),
      fetchJson('/leads'),
      fetchJson('/tasks'),
      fetchJson('/opportunities'),
    ]);

    const dashboardResult = results[0];
    const leadsResult = results[1];
    const tasksResult = results[2];
    const opportunitiesResult = results[3];

    if (dashboardResult.status === 'fulfilled') {
      const raw = asRecord(dashboardResult.value);
      const summary = asRecord(raw.summary);

      setDashboard({
        summary: {
          total_leads: numeric(summary.total_leads),
          hot_leads: numeric(summary.hot_leads),
          warm_leads: numeric(summary.warm_leads),
          cold_leads: numeric(summary.cold_leads),
          opportunities: numeric(summary.opportunities),
          won_opportunities: numeric(summary.won_opportunities),
          conversion_rate: numeric(summary.conversion_rate),
          pipeline_value: numeric(summary.pipeline_value),
          pending_tasks: numeric(summary.pending_tasks),
          overdue_tasks: numeric(summary.overdue_tasks),
          average_lead_score: numeric(summary.average_lead_score),
        },
        opportunity_stages: Array.isArray(raw.opportunity_stages)
          ? raw.opportunity_stages as DashboardData['opportunity_stages']
          : [],
        lead_sources: Array.isArray(raw.lead_sources)
          ? raw.lead_sources as DashboardData['lead_sources']
          : [],
      });
    }

    if (leadsResult.status === 'fulfilled') {
      setLeads(normalizeList(leadsResult.value));
    }

    if (tasksResult.status === 'fulfilled') {
      setTasks(normalizeList(tasksResult.value));
    }

    if (opportunitiesResult.status === 'fulfilled') {
      setOpportunities(normalizeList(opportunitiesResult.value));
    }

    const failures = results
      .map((result, index) => ({
        result,
        name: ['Dashboard', 'Leads', 'Tasks', 'Opportunities'][index],
      }))
      .filter((item) => item.result.status === 'rejected')
      .map((item) => item.name);

    if (failures.length > 0) {
      setError(`Could not load: ${failures.join(', ')}. Check that the backend is running.`);
    }

    setLastUpdated(new Date().toLocaleTimeString());
    setLoading(false);
  }, [fetchJson]);

  useEffect(() => {
    void loadApplication();
  }, [loadApplication]);

  const summary = dashboard.summary;

  const filteredLeads = useMemo(() => {
    const query = searchTerm.trim().toLowerCase();
    if (!query) return leads;

    return leads.filter((lead) => {
      const searchable = [
        getLeadName(lead),
        read(lead, 'email'),
        read(lead, 'company_name', 'company'),
        read(lead, 'source'),
        read(lead, 'status'),
      ].join(' ').toLowerCase();

      return searchable.includes(query);
    });
  }, [leads, searchTerm]);

  const filteredTasks = useMemo(() => {
    const query = searchTerm.trim().toLowerCase();
    if (!query) return tasks;

    return tasks.filter((task) =>
      JSON.stringify(task).toLowerCase().includes(query),
    );
  }, [tasks, searchTerm]);

  const filteredOpportunities = useMemo(() => {
    const query = searchTerm.trim().toLowerCase();
    if (!query) return opportunities;

    return opportunities.filter((opportunity) =>
      JSON.stringify(opportunity).toLowerCase().includes(query),
    );
  }, [opportunities, searchTerm]);

  const navigate = (page: string) => {
    setActivePage(page);
    setSearchTerm('');
    setSidebarOpen(false);
  };

  const navigation = [
    { label: 'Dashboard', icon: LayoutDashboard },
    { label: 'Leads', icon: Users },
    { label: 'Tasks', icon: ClipboardList },
    { label: 'Opportunities', icon: Target },
  ];

  return (
    <div className="app-shell">
      {sidebarOpen && (
        <button
          className="sidebar-overlay"
          aria-label="Close navigation"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside className={`sidebar ${sidebarOpen ? 'sidebar-open' : ''}`}>
        <div className="brand">
          <div className="brand-mark">
            <Zap size={22} fill="currentColor" />
          </div>
          <div className="brand-copy">
            <h2>NexLead</h2>
            <span>SALES INTELLIGENCE</span>
          </div>
          <button
            className="mobile-close"
            onClick={() => setSidebarOpen(false)}
            aria-label="Close menu"
          >
            <X size={19} />
          </button>
        </div>

        <div className="sidebar-section-label">WORKSPACE</div>

        <nav className="sidebar-nav">
          {navigation.map((item) => {
            const Icon = item.icon;
            const active = activePage === item.label;

            return (
              <button
                key={item.label}
                className={`nav-item ${active ? 'active' : ''}`}
                onClick={() => navigate(item.label)}
              >
                <Icon size={19} strokeWidth={2} />
                <span>{item.label}</span>
                {item.label === 'Leads' && (
                  <span className="nav-count">{summary.total_leads}</span>
                )}
              </button>
            );
          })}
        </nav>

        <div className="sidebar-bottom">
          <div className="sidebar-plan">
            <div className="plan-icon"><BarChart3 size={18} /></div>
            <div>
              <strong>NexLead Analytics</strong>
              <span>Lead intelligence platform</span>
            </div>
          </div>

          <div className="profile">
            <div className="profile-avatar">N</div>
            <div className="profile-info">
              <strong>Sales Workspace</strong>
              <span>Administrator</span>
            </div>
            <ChevronDown size={16} />
          </div>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="topbar-left">
            <button
              className="menu-toggle"
              onClick={() => setSidebarOpen(true)}
              aria-label="Open menu"
            >
              <Menu size={21} />
            </button>
            <div>
              <div className="breadcrumb">Workspace <span>/</span> {activePage}</div>
              <h1>{activePage}</h1>
            </div>
          </div>

          <div className="topbar-actions">
            <div className="topbar-search">
              <Search size={17} />
              <input
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
                placeholder={`Search ${activePage.toLowerCase()}...`}
              />
              <kbd>âŒ˜ K</kbd>
            </div>

            <button
              className="icon-button"
              onClick={() => void loadApplication()}
              title="Refresh data"
              aria-label="Refresh data"
            >
              <RefreshCw size={18} className={loading ? 'spin' : ''} />
            </button>

            <button className="icon-button notification-button" title="Notifications">
              <Bell size={18} />
              <span />
            </button>

            <div className="topbar-avatar">N</div>
          </div>
        </header>

        <div className="page-content">
          {error && (
            <div className="error-banner">
              <AlertCircle size={18} />
              <span>{error}</span>
              <button onClick={() => void loadApplication()}>Retry</button>
            </div>
          )}

          {activePage === 'Dashboard' && (
            <DashboardPage
              summary={summary}
              dashboard={dashboard}
              leads={leads}
              tasks={tasks}
              opportunities={opportunities}
              loading={loading}
              lastUpdated={lastUpdated}
              onNavigate={navigate}
            />
          )}

          {activePage === 'Leads' && (
            <LeadsPage
              leads={filteredLeads}
              loading={loading}
              searchTerm={searchTerm}
            />
          )}

          {activePage === 'Tasks' && (
            <TasksPage
              tasks={filteredTasks}
              loading={loading}
            />
          )}

          {activePage === 'Opportunities' && (
            <OpportunitiesPage
              opportunities={filteredOpportunities}
              loading={loading}
            />
          )}
        </div>
      </main>
    </div>
  );
}

type DashboardPageProps = {
  summary: DashboardData['summary'];
  dashboard: DashboardData;
  leads: RecordData[];
  tasks: RecordData[];
  opportunities: RecordData[];
  loading: boolean;
  lastUpdated: string;
  onNavigate: (page: string) => void;
};

function DashboardPage({
  summary,
  dashboard,
  leads,
  tasks,
  opportunities,
  loading,
  lastUpdated,
  onNavigate,
}: DashboardPageProps) {
  const metrics = [
    {
      label: 'Total Leads',
      value: summary.total_leads.toLocaleString(),
      detail: `${summary.hot_leads} hot leads`,
      icon: Users,
      trend: 'Lead database',
    },
    {
      label: 'Opportunities',
      value: summary.opportunities.toLocaleString(),
      detail: `${summary.won_opportunities} won`,
      icon: Target,
      trend: 'Sales pipeline',
    },
    {
      label: 'Pipeline Value',
      value: money(summary.pipeline_value),
      detail: 'Current opportunity value',
      icon: CircleDollarSign,
      trend: 'Pipeline health',
    },
    {
      label: 'Conversion Rate',
      value: `${summary.conversion_rate}%`,
      detail: 'Won opportunities',
      icon: Activity,
      trend: 'Performance',
    },
  ];

  const maxStage = Math.max(
    1,
    ...dashboard.opportunity_stages.map((item) => numeric(item.count)),
  );

  const maxSource = Math.max(
    1,
    ...dashboard.lead_sources.map((item) => numeric(item.count)),
  );

  return (
    <>
      <div className="welcome-row">
        <div>
          <div className="eyebrow">OVERVIEW</div>
          <h2>Sales performance at a glance</h2>
          <p>Monitor leads, pipeline activity, and your team's follow-ups.</p>
        </div>

        <div className="welcome-actions">
          <span className="updated-label">
            <span className="live-dot" />
            {loading ? 'Updating...' : `Updated ${lastUpdated || 'â€”'}`}
          </span>
        </div>
      </div>

      <section className="metrics-grid">
        {metrics.map((metric) => {
          const Icon = metric.icon;

          return (
            <div className="metric-card" key={metric.label}>
              <div className="metric-top">
                <span>{metric.label}</span>
                <div className="metric-icon"><Icon size={19} /></div>
              </div>
              <div className="metric-value">
                {loading ? 'â€”' : metric.value}
              </div>
              <div className="metric-bottom">
                <span>{metric.detail}</span>
                <span className="metric-trend">{metric.trend}</span>
              </div>
            </div>
          );
        })}
      </section>

      <section className="dashboard-grid">
        <div className="panel pipeline-panel">
          <div className="panel-heading">
            <div>
              <h3>Opportunity pipeline</h3>
              <p>Distribution across sales stages</p>
            </div>
            <button className="text-button" onClick={() => onNavigate('Opportunities')}>
              View all <ArrowUpRight size={15} />
            </button>
          </div>

          {dashboard.opportunity_stages.length === 0 ? (
            <EmptyState text="No opportunity stage data available." />
          ) : (
            <div className="bar-list">
              {dashboard.opportunity_stages.map((item) => (
                <div className="bar-item" key={item.stage}>
                  <div className="bar-label">
                    <span>{item.stage}</span>
                    <strong>{item.count}</strong>
                  </div>
                  <div className="bar-track">
                    <div
                      className="bar-fill"
                      style={{ width: `${(numeric(item.count) / maxStage) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="panel source-panel">
          <div className="panel-heading">
            <div>
              <h3>Lead sources</h3>
              <p>Where your leads come from</p>
            </div>
            <div className="panel-icon"><Filter size={17} /></div>
          </div>

          {dashboard.lead_sources.length === 0 ? (
            <EmptyState text="No lead source data available." />
          ) : (
            <div className="source-list">
              {dashboard.lead_sources.map((item) => (
                <div className="source-item" key={item.source}>
                  <div className="source-name">
                    <span className="source-dot" />
                    <span>{item.source}</span>
                  </div>
                  <div className="source-count">
                    <strong>{item.count}</strong>
                    <div className="source-track">
                      <div
                        className="source-fill"
                        style={{ width: `${(numeric(item.count) / maxSource) * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      <section className="metrics-grid secondary-metrics">
        <div className="mini-metric">
          <div className="mini-metric-icon hot"><Zap size={18} /></div>
          <div><span>Hot leads</span><strong>{summary.hot_leads}</strong></div>
        </div>
        <div className="mini-metric">
          <div className="mini-metric-icon warm"><Activity size={18} /></div>
          <div><span>Warm leads</span><strong>{summary.warm_leads}</strong></div>
        </div>
        <div className="mini-metric">
          <div className="mini-metric-icon cold"><Users size={18} /></div>
          <div><span>Cold leads</span><strong>{summary.cold_leads}</strong></div>
        </div>
        <div className="mini-metric">
          <div className="mini-metric-icon task"><Clock3 size={18} /></div>
          <div>
            <span>Pending tasks</span>
            <strong>{summary.pending_tasks}</strong>
            <small>{summary.overdue_tasks} overdue</small>
          </div>
        </div>
      </section>

      <section className="dashboard-grid lower-grid">
        <div className="panel table-panel">
          <div className="panel-heading">
            <div>
              <h3>Recent leads</h3>
              <p>Latest leads added to your workspace</p>
            </div>
            <button className="text-button" onClick={() => onNavigate('Leads')}>
              View all <ArrowUpRight size={15} />
            </button>
          </div>
          <LeadsTable leads={leads.slice(0, 5)} />
        </div>

        <div className="panel task-panel">
          <div className="panel-heading">
            <div>
              <h3>Follow-up tasks</h3>
              <p>Tasks requiring attention</p>
            </div>
            <button className="text-button" onClick={() => onNavigate('Tasks')}>
              View all <ArrowUpRight size={15} />
            </button>
          </div>
          {tasks.length === 0 ? (
            <EmptyState text="No tasks available." />
          ) : (
            <div className="compact-list">
              {tasks.slice(0, 5).map((task, index) => {
                const title = display(read(task, 'title', 'subject', 'description'), 'Follow-up task');
                const status = display(read(task, 'status'), 'Pending');

                return (
                  <div className="compact-item" key={display(read(task, 'id', 'task_id'), String(index))}>
                    <div className="compact-icon"><ClipboardList size={17} /></div>
                    <div className="compact-content">
                      <strong>{title}</strong>
                      <span>{display(read(task, 'due_date', 'due_at'), 'No due date')}</span>
                    </div>
                    <span className={getStatusClass(status)}>{status}</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </section>

      <section className="panel table-panel opportunity-preview">
        <div className="panel-heading">
          <div>
            <h3>Recent opportunities</h3>
            <p>Track deals moving through your pipeline</p>
          </div>
          <button className="text-button" onClick={() => onNavigate('Opportunities')}>
            View all <ArrowUpRight size={15} />
          </button>
        </div>
        <OpportunitiesTable opportunities={opportunities.slice(0, 5)} />
      </section>
    </>
  );
}

function LeadsPage({
  leads,
  loading,
  searchTerm,
}: {
  leads: RecordData[];
  loading: boolean;
  searchTerm: string;
}) {
  return (
    <>
      <div className="welcome-row">
        <div>
          <div className="eyebrow">CUSTOMER ACQUISITION</div>
          <h2>Lead management</h2>
          <p>Review, search, and track your potential customers.</p>
        </div>
        <div className="page-stat">
          <strong>{leads.length}</strong>
          <span>{searchTerm ? 'Matching leads' : 'Available leads'}</span>
        </div>
      </div>

      <div className="panel table-panel full-table-panel">
        <div className="panel-heading">
          <div>
            <h3>All leads</h3>
            <p>Lead records from your CRM database</p>
          </div>
          <span className="table-count">{leads.length} records</span>
        </div>
        {loading ? <LoadingState /> : <LeadsTable leads={leads} />}
      </div>
    </>
  );
}

function TasksPage({
  tasks,
  loading,
}: {
  tasks: RecordData[];
  loading: boolean;
}) {
  return (
    <>
      <div className="welcome-row">
        <div>
          <div className="eyebrow">WORK MANAGEMENT</div>
          <h2>Follow-up tasks</h2>
          <p>Keep track of the next actions needed to move leads forward.</p>
        </div>
        <div className="page-stat">
          <strong>{tasks.length}</strong>
          <span>Tasks in workspace</span>
        </div>
      </div>

      <div className="panel table-panel full-table-panel">
        <div className="panel-heading">
          <div>
            <h3>All tasks</h3>
            <p>Assigned follow-ups and sales activities</p>
          </div>
          <span className="table-count">{tasks.length} records</span>
        </div>
        {loading ? <LoadingState /> : <TasksTable tasks={tasks} />}
      </div>
    </>
  );
}

function OpportunitiesPage({
  opportunities,
  loading,
}: {
  opportunities: RecordData[];
  loading: boolean;
}) {
  return (
    <>
      <div className="welcome-row">
        <div>
          <div className="eyebrow">REVENUE MANAGEMENT</div>
          <h2>Sales opportunities</h2>
          <p>Monitor deal stages, expected revenue, and outcomes.</p>
        </div>
        <div className="page-stat">
          <strong>{opportunities.length}</strong>
          <span>Active records</span>
        </div>
      </div>

      <div className="panel table-panel full-table-panel">
        <div className="panel-heading">
          <div>
            <h3>All opportunities</h3>
            <p>Sales pipeline records</p>
          </div>
          <span className="table-count">{opportunities.length} records</span>
        </div>
        {loading ? <LoadingState /> : <OpportunitiesTable opportunities={opportunities} />}
      </div>
    </>
  );
}

function LeadsTable({ leads }: { leads: RecordData[] }) {
  if (leads.length === 0) {
    return <EmptyState text="No leads found." />;
  }

  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>LEAD</th>
            <th>COMPANY</th>
            <th>SOURCE</th>
            <th>SCORE</th>
            <th>STATUS</th>
          </tr>
        </thead>
        <tbody>
          {leads.map((lead, index) => {
            const name = getLeadName(lead);
            const email = display(read(lead, 'email'), 'No email');
            const company = display(read(lead, 'company_name', 'company'), 'â€”');
            const source = display(read(lead, 'source', 'lead_source'), 'â€”');
            const score = numeric(read(lead, 'score', 'lead_score'));
            const status = display(read(lead, 'status', 'temperature'), 'New');

            return (
              <tr key={display(read(lead, 'id', 'lead_id'), String(index))}>
                <td>
                  <div className="table-person">
                    <div className="person-avatar">{name.charAt(0).toUpperCase()}</div>
                    <div>
                      <strong>{name}</strong>
                      <span>{email}</span>
                    </div>
                  </div>
                </td>
                <td>{company}</td>
                <td>{source}</td>
                <td>
                  <div className="score-cell">
                    <strong>{score}</strong>
                    <span>/100</span>
                  </div>
                </td>
                <td><span className={getStatusClass(status)}>{status}</span></td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function TasksTable({ tasks }: { tasks: RecordData[] }) {
  if (tasks.length === 0) {
    return <EmptyState text="No tasks found." />;
  }

  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>TASK</th>
            <th>LEAD</th>
            <th>ASSIGNEE</th>
            <th>DUE DATE</th>
            <th>STATUS</th>
          </tr>
        </thead>
        <tbody>
          {tasks.map((task, index) => {
            const title = display(read(task, 'title', 'subject', 'description'), 'Follow-up');
            const lead = display(read(task, 'lead_name', 'lead'), 'â€”');
            const assignee = display(read(task, 'assigned_to_name', 'assignee', 'sales_rep'), 'â€”');
            const due = display(read(task, 'due_date', 'due_at'), 'â€”');
            const status = display(read(task, 'status'), 'Pending');

            return (
              <tr key={display(read(task, 'id', 'task_id'), String(index))}>
                <td><strong>{title}</strong></td>
                <td>{lead}</td>
                <td>{assignee}</td>
                <td>{due}</td>
                <td><span className={getStatusClass(status)}>{status}</span></td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function OpportunitiesTable({
  opportunities,
}: {
  opportunities: RecordData[];
}) {
  if (opportunities.length === 0) {
    return <EmptyState text="No opportunities found." />;
  }

  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>OPPORTUNITY</th>
            <th>LEAD</th>
            <th>STAGE</th>
            <th>VALUE</th>
            <th>STATUS</th>
          </tr>
        </thead>
        <tbody>
          {opportunities.map((opportunity, index) => {
            const name = display(read(opportunity, 'name', 'title'), 'Sales opportunity');
            const lead = display(read(opportunity, 'lead_name', 'lead'), 'â€”');
            const stage = display(read(opportunity, 'stage'), 'Qualified');
            const value = money(read(opportunity, 'value', 'amount', 'expected_revenue'));
            const status = display(read(opportunity, 'status'), stage);

            return (
              <tr key={display(read(opportunity, 'id', 'opportunity_id'), String(index))}>
                <td><strong>{name}</strong></td>
                <td>{lead}</td>
                <td><span className={getStatusClass(stage)}>{stage}</span></td>
                <td><strong>{value}</strong></td>
                <td><span className={getStatusClass(status)}>{status}</span></td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="empty-state">
      <div className="empty-icon"><Building2 size={21} /></div>
      <p>{text}</p>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="loading-state">
      <RefreshCw size={19} className="spin" />
      <span>Loading records...</span>
    </div>
  );
}

export default App;

