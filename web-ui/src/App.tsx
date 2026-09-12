// src/App.tsx
import { useState, useEffect, useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

// ============================================================
// SECTION: Types
// ============================================================
interface KPISummary {
  data_assets: number;
  tables_scanned: number;
  pii_columns: number;
  policy_violations: number;
}

interface Proposal {
  proposal_id: string;
  dataset_urn: string;
  action_type: string;
  target_column: string;
  description: string;
}

interface PIIDistribution {
  high_risk: number;
  medium_risk: number;
  low_risk: number;
  total: number;
  high_pct: number;
  medium_pct: number;
  low_pct: number;
}

interface QualityIssue {
  type: string;
  column: string;
  percentage: number;
}

interface QualityInsights {
  overall_score: number;
  total_issues: number;
  top_issues: QualityIssue[];
}

interface LineageNode {
  id: string;
  table: string;
  domain: string;
  stage: 'raw' | 'staging' | 'mart';
  col_count: number;
  has_pii: boolean;
}

interface LineageEdge {
  source: string;
  target: string;
}

interface LineageGraph {
  nodes: LineageNode[];
  edges: LineageEdge[];
}
//-----
interface ActivityEvent {
  timestamp: string;
  action: string;
  patch_id: string;
  dataset_urn: string | null;
  patch_type: string | null;
  target_column: string | null;
  rows_updated: number;
}
//----
interface MetricPoint {
  t: number;
  v: number;
}

type MetricKey = 'pii' | 'quality' | 'violations' | 'proposals';

const METRIC_CONFIG: Record<MetricKey, { label: string; color: string }> = {
  pii: { label: 'PII Columns', color: '#fbbf24' },
  quality: { label: 'Quality Score', color: '#34d399' },
  violations: { label: 'Policy Violations', color: '#f87171' },
  proposals: { label: 'Pending Proposals', color: '#a78bfa' },
};

const API_BASE = 'http://localhost:8000';
const STAGE_ORDER: Record<string, number> = { raw: 0, staging: 1, mart: 2 };

// ============================================================
// SECTION: Lineage map — простая позиционная раскладка + SVG-линии
// ============================================================
function LineageMap({ graph }: { graph: LineageGraph }) {
  const domains = useMemo(
    () => Array.from(new Set(graph.nodes.map((n) => n.domain))),
    [graph.nodes]
  );
  const [activeDomain, setActiveDomain] = useState(domains[0] || '');

  useEffect(() => {
    if (domains.length > 0 && !domains.includes(activeDomain)) {
      setActiveDomain(domains[0]);
    }
  }, [domains]);

  const filteredNodes = graph.nodes.filter((n) => n.domain === activeDomain);
  const filteredEdges = graph.edges.filter(
    (e) => filteredNodes.some((n) => n.id === e.source) && filteredNodes.some((n) => n.id === e.target)
  );

  const NODE_W = 150;
  const NODE_H = 60;
  const COL_GAP = 210;
  const ROW_GAP = 90;

  const positions = useMemo(() => {
    const byStage: Record<string, LineageNode[]> = { raw: [], staging: [], mart: [] };
    filteredNodes.forEach((n) => byStage[n.stage].push(n));

    const pos: Record<string, { x: number; y: number }> = {};
    (['raw', 'staging', 'mart'] as const).forEach((stage) => {
      byStage[stage].forEach((n, i) => {
        pos[n.id] = { x: STAGE_ORDER[stage] * COL_GAP, y: i * ROW_GAP };
      });
    });
    return pos;
  }, [filteredNodes]);

  const width = 3 * COL_GAP;
  const height = Math.max(...Object.values(positions).map((p) => p.y), 0) + NODE_H + 20;

  return (
    <div>
      <div className="flex gap-1 mb-3">
        {domains.map((d) => (
          <button
            key={d}
            onClick={() => setActiveDomain(d)}
            className="text-[10px] px-2.5 py-1 rounded transition-colors"
            style={
              activeDomain === d
                ? { backgroundColor: 'var(--color-accent-bg)', color: 'var(--color-accent-hover)', border: '1px solid var(--color-accent-border)' }
                : { backgroundColor: 'var(--color-bg-card-alt)', color: 'var(--color-text-muted)', border: '1px solid var(--color-border)' }
            }
          >
            {d}
          </button>
        ))}
      </div>

      <div className="relative overflow-auto" style={{ width: '100%', height: Math.min(height, 420) }}>
        <svg width={width} height={height} className="absolute top-0 left-0 pointer-events-none">
          {filteredEdges.map((e, i) => {
            const s = positions[e.source];
            const t = positions[e.target];
            if (!s || !t) return null;
            const x1 = s.x + NODE_W;
            const y1 = s.y + NODE_H / 2;
            const x2 = t.x;
            const y2 = t.y + NODE_H / 2;
            const midX = (x1 + x2) / 2;
            return (
              <path
                key={i}
                d={`M ${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2} ${y2}`}
                stroke="#7dd3fc"
                strokeWidth="1.5"
                strokeDasharray="4 3"
                fill="none"
              />
            );
          })}
        </svg>

        {filteredNodes.map((n) => {
          const p = positions[n.id];
          if (!p) return null;
          return (
            <div
              key={n.id}
              className="absolute rounded-lg px-3 py-2 transition-colors"
              style={{
                left: p.x, top: p.y, width: NODE_W, height: NODE_H,
                backgroundColor: 'var(--color-bg-card)',
                border: '1px solid var(--color-accent-border)',
              }}
            >
              <div className="flex items-center justify-between gap-1">
                <span className="text-xs font-medium truncate" style={{ color: 'var(--color-text-primary)' }}>{n.table}</span>
                {n.has_pii && (
                  <span className="text-[9px] px-1 rounded shrink-0" style={{ backgroundColor: 'var(--color-danger-bg)', color: 'var(--color-danger)', border: '1px solid var(--color-danger-border)' }}>PII</span>
                )}
              </div>
              <div className="text-[10px] mt-1" style={{ color: 'var(--color-text-muted)' }}>{n.col_count} cols</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ============================================================
// SECTION: Sidebar
// ============================================================
const NAV_ITEMS = [
  'Overview', 'Data Assets', 'Lineage Map', 'Data Profiling',
  'Policy Rules', 'Pending Proposals', 'Approvals', 'Activity Log', 'Settings',
];

function Sidebar({ active, onSelect }: { active: string; onSelect: (item: string) => void }) {
  return (
    <aside
      className="w-56 shrink-0 flex flex-col p-4"
      style={{ borderRight: '1px solid var(--color-border)', backgroundColor: 'var(--color-bg-card)' }}
    >
      <div className="flex items-center gap-2 mb-8">
        <span className="text-xl" style={{ color: 'var(--color-accent)' }}>[]</span>
        <div>
          <div className="text-sm font-bold" style={{ color: 'var(--color-text-primary)' }}>Albugent</div>
          <div className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>Governance Studio</div>
        </div>
      </div>
      <nav className="flex flex-col gap-1">
        {NAV_ITEMS.map((item) => (
          <button
            key={item}
            onClick={() => onSelect(item)}
            className="text-left text-xs px-3 py-2 rounded transition-colors"
            style={
              active === item
                ? { backgroundColor: 'var(--color-accent-bg)', color: 'var(--color-accent-hover)', border: '1px solid var(--color-accent-border)' }
                : { color: 'var(--color-text-secondary)' }
            }
          >
            {item}
          </button>
        ))}
      </nav>
    </aside>
  );
}

function CombinedMetricsChart({ history }: { history: Record<MetricKey, MetricPoint[]> }) {
  const length = history.quality.length;
  if (length === 0) return null;

  const logTransform = (points: MetricPoint[]) => points.map((p) => Math.log(p.v + 1));

  const logValues: Record<MetricKey, number[]> = {
    pii: logTransform(history.pii),
    quality: logTransform(history.quality),
    violations: logTransform(history.violations),
    proposals: logTransform(history.proposals),
  };

  const chartData = Array.from({ length }, (_, i) => ({
    time: new Date(history.quality[i]?.t ?? Date.now()).toLocaleTimeString(),
    pii: logValues.pii[i],
    pii_real: history.pii[i]?.v,
    quality: logValues.quality[i],
    quality_real: history.quality[i]?.v,
    violations: logValues.violations[i],
    violations_real: history.violations[i]?.v,
    proposals: logValues.proposals[i],
    proposals_real: history.proposals[i]?.v,
  }));

  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart data={chartData}>
        <XAxis dataKey="time" hide />
        <YAxis hide domain={['auto', 'auto']} />
        <Tooltip
          contentStyle={{ background: '#0a0a0f', border: '1px solid #27272a', fontSize: 11 }}
          formatter={((_value: any, name: any, props: any) => {
            const key = String(name).replace('_real', '') as MetricKey;
            return [props.payload[`${key}_real`], METRIC_CONFIG[key]?.label ?? name];
          }) as any}
        />
        {(Object.keys(METRIC_CONFIG) as MetricKey[]).map((key) => (
          <Line
            key={key}
            type="monotone"
            dataKey={key}
            name={`${key}_real`}
            stroke={METRIC_CONFIG[key].color}
            strokeWidth={2}
            dot={false}
            isAnimationActive={true}
            animationDuration={400}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

// ============================================================
// SECTION: Main App
// ============================================================
function ActivityLogView({ events }: { events: ActivityEvent[] }) {
  if (events.length === 0) {
    return <div className="text-xs text-gray-600 text-center py-12">No activity yet.</div>;
  }
  return (
    <div className="space-y-2">
      {events.map((e, i) => (
        <div key={i} className="flex items-center justify-between p-3 bg-black border border-gray-800 rounded text-xs">
          <div>
            <span className={e.action === 'approve' ? 'text-emerald-400 font-bold' : 'text-red-400 font-bold'}>
              {e.action.toUpperCase()}
            </span>
            <span className="text-gray-400 ml-2">{e.patch_id}</span>
            {e.target_column && <span className="text-gray-600 ml-2">→ {e.target_column}</span>}
          </div>
          <span className="text-gray-600">{new Date(e.timestamp).toLocaleString()}</span>
        </div>
      ))}
    </div>
  );
}

export default function App() {
  const [activeNav, setActiveNav] = useState('Overview');
  const [kpi, setKpi] = useState<KPISummary | null>(null);
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [piiDist, setPiiDist] = useState<PIIDistribution | null>(null);
  const [quality, setQuality] = useState<QualityInsights | null>(null);
  const [lineage, setLineage] = useState<LineageGraph | null>(null);
  const [loading, setLoading] = useState(true);
  const [applyingId, setApplyingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [generatingPR, setGeneratingPR] = useState(false);
  const [prResult, setPrResult] = useState<{ status: string; pr_url?: string; message?: string } | null>(null);
  const [activityLog, setActivityLog] = useState<ActivityEvent[]>([]); //new one 
  const [history, setHistory] = useState<Record<MetricKey, MetricPoint[]>>({
    pii: [], quality: [], violations: [], proposals: [],
  });


  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [kpiRes, proposalsRes, piiRes, qualityRes, lineageRes, activityRes] = await Promise.all([
        fetch(`${API_BASE}/api/kpi-summary`),
        fetch(`${API_BASE}/api/proposals`),
        fetch(`${API_BASE}/api/pii-distribution`),
        fetch(`${API_BASE}/api/quality-insights`),
        fetch(`${API_BASE}/api/lineage-graph`),
        fetch(`${API_BASE}/api/activity-log`),
      ]);
      if (!kpiRes.ok || !proposalsRes.ok || !piiRes.ok || !qualityRes.ok || !lineageRes.ok) {
        throw new Error('Backend request failed');
      }
      const activityData = await activityRes.json();
      setKpi(await kpiRes.json());
      setProposals(await proposalsRes.json());
      setPiiDist(await piiRes.json());
      setQuality(await qualityRes.json());
      setLineage(await lineageRes.json());
    } catch (err: any) {
      setError(err.message || 'Failed to reach backend');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);
  // ============================================================
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const [kpiRes, proposalsRes, qualityRes] = await Promise.all([
          fetch(`${API_BASE}/api/kpi-summary`),
          fetch(`${API_BASE}/api/proposals`),
          fetch(`${API_BASE}/api/quality-insights`),
        ]);
        const kpiData: KPISummary = await kpiRes.json();
        const proposalsData: Proposal[] = await proposalsRes.json();
        const qualityData: QualityInsights = await qualityRes.json();
        const t = Date.now();

        setHistory((prev) => ({
          pii: [...prev.pii, { t, v: kpiData.pii_columns }].slice(-30),
          quality: [...prev.quality, { t, v: qualityData.overall_score }].slice(-30),
          violations: [...prev.violations, { t, v: kpiData.policy_violations }].slice(-30),
          proposals: [...prev.proposals, { t, v: proposalsData.length }].slice(-30),
        }));
      } catch {
        // тихо пропускаем один неудачный poll, не рвём весь график
      }
    }, 5000);

    return () => clearInterval(interval);
  }, []);
  // ============================================================
  const handleApprove = async (proposal: Proposal) => {
    setApplyingId(proposal.proposal_id);
    try {
      const url = `${API_BASE}/api/proposals/${encodeURIComponent(proposal.proposal_id)}/approve?dataset_urn=${encodeURIComponent(proposal.dataset_urn)}`;
      const res = await fetch(url, { method: 'POST' });
      const result = await res.json();
      if (result.error) throw new Error(result.error);
      setProposals((prev) => prev.filter((p) => p.proposal_id !== proposal.proposal_id));
    } catch (err: any) {
      alert(`Failed to apply: ${err.message}`);
    } finally {
      setApplyingId(null);
    }
  };

  const handleReject = async (proposal: Proposal) => {
    try {
      await fetch(`${API_BASE}/api/proposals/${encodeURIComponent(proposal.proposal_id)}/reject`, { method: 'POST' });
    } finally {
      setProposals((prev) => prev.filter((p) => p.proposal_id !== proposal.proposal_id));
    }
  };

  const handleGeneratePR = async () => {
    setGeneratingPR(true);
    setPrResult(null);
    try {
      const res = await fetch(`${API_BASE}/api/generate-pr`, { method: 'POST' });
      const result = await res.json();
      setPrResult(result);
    } catch (err: any) {
      setPrResult({ status: 'error', message: err.message || 'Request failed' });
    } finally {
      setGeneratingPR(false);
    }
  };

  return (
    <div className="h-screen font-mono flex overflow-hidden" style={{ backgroundColor: 'var(--color-bg-page)', color: 'var(--color-text-primary)' }}>
      <Sidebar active={activeNav} onSelect={setActiveNav} />

      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header
          className="px-6 py-4 flex items-center justify-between shrink-0"
          style={{ borderBottom: '1px solid var(--color-border)' }}
        >
          <div>
            <h1 className="text-lg font-bold" style={{ color: 'var(--color-text-primary)' }}>Governance Overview</h1>
            <div className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>Deterministic. Transparent. Trusted.</div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleGeneratePR}
              disabled={generatingPR}
              className="text-xs disabled:opacity-50 px-3 py-1.5 rounded font-bold transition-colors"
              style={{ backgroundColor: 'var(--color-accent)', color: '#ffffff' }}
            >
              {generatingPR ? 'Generating PR...' : 'Generate PR'}
            </button>
            <button
              onClick={loadData}
              className="text-xs px-3 py-1.5 rounded transition-colors"
              style={{ backgroundColor: 'var(--color-bg-card-alt)', border: '1px solid var(--color-border)', color: 'var(--color-text-secondary)' }}
            >
              Refresh
            </button>
          </div>
        </header>
        {prResult && (
          <div
            className="px-6 py-2 text-xs shrink-0"
            style={
              prResult.status === 'success'
                ? { backgroundColor: 'var(--color-success-bg)', borderBottom: '1px solid var(--color-success-border)', color: 'var(--color-success)' }
                : { backgroundColor: 'var(--color-danger-bg)', borderBottom: '1px solid var(--color-danger-border)', color: 'var(--color-danger)' }
            }
          >
            {prResult.status === 'success' ? (
              <>
                ✅ PR created:{' '}
                <a href={prResult.pr_url} target="_blank" rel="noopener noreferrer" className="underline font-bold">
                  {prResult.pr_url}
                </a>
              </>
            ) : (
              <>❌ Failed to generate PR: {prResult.message}</>
            )}
          </div>
        )}

        <main className="flex-1 p-6 flex flex-col gap-6 overflow-y-auto">
          {activeNav === 'Overview' && (
            <>
              {error && (
                <div className="bg-red-950/40 border border-red-900 text-red-300 text-sm p-3 rounded shrink-0">
                  {error} — is uvicorn running on :8000?
                </div>
              )}

              {/* KPI Banner */}
              <div className="grid grid-cols-4 gap-4 shrink-0">
                <div className="rounded-lg p-4" style={{ backgroundColor: 'var(--color-bg-card)', border: '1px solid var(--color-border)' }}>
                  <div className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>Data Assets</div>
                  <div className="text-2xl font-bold mt-1" style={{ color: 'var(--color-text-primary)' }}>{loading ? '...' : kpi?.data_assets ?? 0}</div>
                </div>
                <div className="rounded-lg p-4" style={{ backgroundColor: 'var(--color-bg-card)', border: '1px solid var(--color-border)' }}>
                  <div className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>Tables Scanned</div>
                  <div className="text-2xl font-bold mt-1" style={{ color: 'var(--color-text-primary)' }}>{loading ? '...' : kpi?.tables_scanned ?? 0}</div>
                </div>
                <div className="rounded-lg p-4" style={{ backgroundColor: 'var(--color-bg-card)', border: '1px solid var(--color-border)' }}>
                  <div className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>PII Columns</div>
                  <div className="text-2xl font-bold mt-1" style={{ color: 'var(--color-warning)' }}>{loading ? '...' : kpi?.pii_columns ?? 0}</div>
                </div>
                <div className="rounded-lg p-4" style={{ backgroundColor: 'var(--color-bg-card)', border: '1px solid var(--color-border)' }}>
                  <div className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>Policy Violations</div>
                  <div className="text-2xl font-bold mt-1" style={{ color: 'var(--color-danger)' }}>{loading ? '...' : kpi?.policy_violations ?? 0}</div>
                </div>
              </div>

              {/* Lineage map + Pending proposals */}
              <div className="grid grid-cols-3 gap-6 shrink-0">
                <div className="col-span-2 rounded-lg p-4" style={{ backgroundColor: 'var(--color-bg-card)', border: '1px solid var(--color-border)' }}>
                  <h3 className="text-xs font-semibold tracking-wider uppercase mb-3" style={{ color: 'var(--color-text-secondary)' }}>
                    Downstream Lineage Map
                  </h3>
                  {loading && <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Loading...</div>}
                  {!loading && lineage && <LineageMap graph={lineage} />}
                </div>

                <div className="rounded-lg p-4 flex flex-col overflow-hidden max-h-[480px]" style={{ backgroundColor: 'var(--color-bg-card)', border: '1px solid var(--color-border)' }}>
                  <h3 className="text-xs font-semibold tracking-wider uppercase mb-3" style={{ color: 'var(--color-text-secondary)' }}>
                    Pending Proposals ({proposals.length})
                  </h3>
                  {loading && <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Loading...</div>}
                  {!loading && proposals.length === 0 && (
                    <div className="text-xs text-center py-8" style={{ color: 'var(--color-text-muted)' }}>No pending proposals.</div>
                  )}
                  <div className="space-y-2 overflow-y-auto flex-1 pr-1">
                    {proposals.map((p) => (
                      <div key={p.proposal_id} className="p-2.5 rounded space-y-1.5" style={{ backgroundColor: 'var(--color-bg-card-alt)', border: '1px solid var(--color-border)' }}>
                        <div className="text-xs font-bold" style={{ color: 'var(--color-text-primary)' }}>{p.action_type}</div>
                        <div className="text-[10px] break-all" style={{ color: 'var(--color-text-muted)' }}>{p.dataset_urn.split(',')[1]}</div>
                        <div className="text-[10px]" style={{ color: 'var(--color-text-secondary)' }}>{p.description}</div>
                        <div className="flex gap-1.5 pt-1">
                          <button
                            onClick={() => handleApprove(p)}
                            disabled={applyingId === p.proposal_id}
                            className="flex-1 disabled:opacity-50 text-[10px] py-1 rounded font-bold transition-colors"
                            style={{ backgroundColor: 'var(--color-success-bg)', border: '1px solid var(--color-success-border)', color: 'var(--color-success)' }}
                          >
                            {applyingId === p.proposal_id ? '...' : 'APPROVE'}
                          </button>
                          <button
                            onClick={() => handleReject(p)}
                            disabled={applyingId === p.proposal_id}
                            className="flex-1 disabled:opacity-50 text-[10px] py-1 rounded font-bold transition-colors"
                            style={{ backgroundColor: 'var(--color-danger-bg)', border: '1px solid var(--color-danger-border)', color: 'var(--color-danger)' }}
                          >
                            REJECT
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              {/* Live Metrics — все линии в одном графике */}
              <div className="rounded-lg p-4 shrink-0" style={{ backgroundColor: 'var(--color-bg-card)', border: '1px solid var(--color-border)' }}>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-xs font-semibold tracking-wider uppercase" style={{ color: 'var(--color-text-secondary)' }}>Live Metrics</h3>
                  <div className="flex gap-3">
                    {(Object.keys(METRIC_CONFIG) as MetricKey[]).map((key) => (
                      <div key={key} className="flex items-center gap-1.5 text-[10px]">
                        <span className="w-2 h-2 rounded-full" style={{ backgroundColor: METRIC_CONFIG[key].color }}></span>
                        <span style={{ color: 'var(--color-text-secondary)' }}>{METRIC_CONFIG[key].label}</span>
                      </div>
                    ))}
                  </div>
                </div>
                {history.quality.length === 0 ? (
                  <div className="text-xs text-center py-12" style={{ color: 'var(--color-text-muted)' }}>
                    Collecting data... first point in a few seconds.
                  </div>
                ) : (
                  <CombinedMetricsChart history={history} />
                )}
              </div>

              {/* Quality Insights + PII Distribution */}
              <div className="grid grid-cols-2 gap-6 shrink-0">
                <div className="rounded-lg p-4" style={{ backgroundColor: 'var(--color-bg-card)', border: '1px solid var(--color-border)' }}>
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-xs font-semibold tracking-wider uppercase" style={{ color: 'var(--color-text-secondary)' }}>Data Quality Insights</h3>
                    <span className="text-2xl font-bold" style={{ color: 'var(--color-success)' }}>{loading ? '...' : quality?.overall_score ?? 0}</span>
                  </div>
                  {!loading && (quality?.top_issues.length ?? 0) === 0 && (
                    <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>No active quality issues detected.</div>
                  )}
                  <div className="space-y-2">
                    {quality?.top_issues.map((issue, i) => (
                      <div key={i} className="flex items-center justify-between text-xs pb-2" style={{ borderBottom: '1px solid var(--color-border)' }}>
                        <div>
                          <div style={{ color: 'var(--color-text-primary)' }}>{issue.type}</div>
                          <div className="text-[11px]" style={{ color: 'var(--color-text-muted)' }}>{issue.column}</div>
                        </div>
                        <span className="font-bold shrink-0 ml-2" style={{ color: 'var(--color-warning)' }}>{issue.percentage}%</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="rounded-lg p-4" style={{ backgroundColor: 'var(--color-bg-card)', border: '1px solid var(--color-border)' }}>
                  <h3 className="text-xs font-semibold tracking-wider uppercase mb-3" style={{ color: 'var(--color-text-secondary)' }}>PII Distribution</h3>
                  {!loading && piiDist && (
                    <div className="space-y-3">
                      <div className="flex items-center justify-between text-xs">
                        <span style={{ color: 'var(--color-danger)' }}>High Risk</span>
                        <span style={{ color: 'var(--color-text-secondary)' }}>{piiDist.high_risk} ({piiDist.high_pct}%)</span>
                      </div>
                      <div className="h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: 'var(--color-bg-card-alt)' }}>
                        <div className="h-full" style={{ width: `${piiDist.high_pct}%`, backgroundColor: 'var(--color-danger)' }}></div>
                      </div>

                      <div className="flex items-center justify-between text-xs">
                        <span style={{ color: 'var(--color-warning)' }}>Medium Risk</span>
                        <span style={{ color: 'var(--color-text-secondary)' }}>{piiDist.medium_risk} ({piiDist.medium_pct}%)</span>
                      </div>
                      <div className="h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: 'var(--color-bg-card-alt)' }}>
                        <div className="h-full" style={{ width: `${piiDist.medium_pct}%`, backgroundColor: 'var(--color-warning)' }}></div>
                      </div>

                      <div className="flex items-center justify-between text-xs">
                        <span style={{ color: 'var(--color-success)' }}>Low Risk</span>
                        <span style={{ color: 'var(--color-text-secondary)' }}>{piiDist.low_risk} ({piiDist.low_pct}%)</span>
                      </div>
                      <div className="h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: 'var(--color-bg-card-alt)' }}>
                        <div className="h-full" style={{ width: `${piiDist.low_pct}%`, backgroundColor: 'var(--color-success)' }}></div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </>
          )}

          {activeNav === 'Activity Log' && (
            <div className="bg-[#0a0a0f] border border-gray-800 rounded-lg p-4">
              <h3 className="text-xs text-gray-400 font-semibold tracking-wider uppercase mb-4">Activity Log</h3>
              <ActivityLogView events={activityLog} />
            </div>
          )}

          {!['Overview', 'Activity Log'].includes(activeNav) && (
            <div className="text-center text-gray-600 text-sm py-20">
              {activeNav} — coming soon
            </div>
          )}
        </main>
      </div>
    </div>
  );
}