// src/App.tsx
import React, { useState, useEffect, useMemo } from 'react';
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
            className={`text-[10px] px-2.5 py-1 rounded transition-colors ${activeDomain === d
                ? 'bg-violet-950 text-violet-300 border border-violet-700'
                : 'bg-gray-900 text-gray-500 border border-gray-800 hover:text-gray-300'
              }`}
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
                stroke="#4c1d95"
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
              className="absolute bg-[#0d0d14] border border-violet-900/60 rounded-lg px-3 py-2 hover:border-violet-500 transition-colors"
              style={{ left: p.x, top: p.y, width: NODE_W, height: NODE_H }}
            >
              <div className="flex items-center justify-between gap-1">
                <span className="text-xs font-medium text-gray-200 truncate">{n.table}</span>
                {n.has_pii && (
                  <span className="text-[9px] bg-red-950 text-red-400 border border-red-800 px-1 rounded shrink-0">PII</span>
                )}
              </div>
              <div className="text-[10px] text-gray-500 mt-1">{n.col_count} cols</div>
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
    <aside className="w-56 shrink-0 border-r border-gray-800 bg-[#08080c] flex flex-col p-4">
      <div className="flex items-center gap-2 mb-8">
        <span className="text-violet-400 text-xl">[]</span>
        <div>
          <div className="text-sm font-bold text-white">Albugent</div>
          <div className="text-[10px] text-gray-500">Governance Studio</div>
        </div>
      </div>
      <nav className="flex flex-col gap-1">
        {NAV_ITEMS.map((item) => (
          <button
            key={item}
            onClick={() => onSelect(item)}
            className={`text-left text-xs px-3 py-2 rounded transition-colors ${active === item
              ? 'bg-violet-950/60 text-violet-300 border border-violet-800'
              : 'text-gray-400 hover:bg-gray-900'
              }`}
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
          formatter={(_value: any, name: string, props: any) => {
            const key = name.replace('_real', '') as MetricKey;
            return [props.payload[`${key}_real`], METRIC_CONFIG[key]?.label ?? name];
          }}
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
  //-----------------------
  const [history, setHistory] = useState<Record<MetricKey, MetricPoint[]>>({
    pii: [], quality: [], violations: [], proposals: [],
  });
  const [selectedMetric, setSelectedMetric] = useState<MetricKey>('quality');
  //-----------------------
  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [kpiRes, proposalsRes, piiRes, qualityRes, lineageRes] = await Promise.all([
        fetch(`${API_BASE}/api/kpi-summary`),
        fetch(`${API_BASE}/api/proposals`),
        fetch(`${API_BASE}/api/pii-distribution`),
        fetch(`${API_BASE}/api/quality-insights`),
        fetch(`${API_BASE}/api/lineage-graph`),
      ]);
      if (!kpiRes.ok || !proposalsRes.ok || !piiRes.ok || !qualityRes.ok || !lineageRes.ok) {
        throw new Error('Backend request failed');
      }
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

  return (
    <div className="h-screen bg-[#060608] text-gray-200 font-mono flex overflow-hidden">
      <Sidebar active={activeNav} onSelect={setActiveNav} />

      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="border-b border-gray-800 px-6 py-4 flex items-center justify-between shrink-0">
          <div>
            <h1 className="text-lg font-bold text-white">Governance Overview</h1>
            <div className="text-xs text-gray-500">Deterministic. Transparent. Trusted.</div>
          </div>
          <button
            onClick={loadData}
            className="text-xs bg-gray-900 hover:bg-gray-800 border border-gray-700 text-gray-300 px-3 py-1.5 rounded transition-colors"
          >
            Refresh
          </button>
        </header>

        <main className="flex-1 p-6 flex flex-col gap-6 overflow-y-auto">
          {error && (
            <div className="bg-red-950/40 border border-red-900 text-red-300 text-sm p-3 rounded shrink-0">
              {error} — is uvicorn running on :8000?
            </div>
          )}

          {/* KPI Banner */}
          <div className="grid grid-cols-4 gap-4 shrink-0">
            <div className="bg-[#0a0a0f] border border-gray-800 rounded-lg p-4">
              <div className="text-xs text-gray-400">Data Assets</div>
              <div className="text-2xl font-bold mt-1">{loading ? '...' : kpi?.data_assets ?? 0}</div>
            </div>
            <div className="bg-[#0a0a0f] border border-gray-800 rounded-lg p-4">
              <div className="text-xs text-gray-400">Tables Scanned</div>
              <div className="text-2xl font-bold mt-1">{loading ? '...' : kpi?.tables_scanned ?? 0}</div>
            </div>
            <div className="bg-[#0a0a0f] border border-gray-800 rounded-lg p-4">
              <div className="text-xs text-gray-400">PII Columns</div>
              <div className="text-2xl font-bold mt-1 text-amber-400">{loading ? '...' : kpi?.pii_columns ?? 0}</div>
            </div>
            <div className="bg-[#0a0a0f] border border-gray-800 rounded-lg p-4">
              <div className="text-xs text-gray-400">Policy Violations</div>
              <div className="text-2xl font-bold mt-1 text-red-400">{loading ? '...' : kpi?.policy_violations ?? 0}</div>
            </div>
          </div>

          {/* Lineage map + Pending proposals */}
          <div className="grid grid-cols-3 gap-6 shrink-0">
            <div className="col-span-2 bg-[#0a0a0f] border border-gray-800 rounded-lg p-4">
              <h3 className="text-xs text-gray-400 font-semibold tracking-wider uppercase mb-3">
                Downstream Lineage Map
              </h3>
              {loading && <div className="text-xs text-gray-600">Loading...</div>}
              {!loading && lineage && <LineageMap graph={lineage} />}
            </div>

            <div className="bg-[#0a0a0f] border border-gray-800 rounded-lg p-4 flex flex-col overflow-hidden max-h-[480px]">
              <h3 className="text-xs text-gray-400 font-semibold tracking-wider uppercase mb-3">
                Pending Proposals ({proposals.length})
              </h3>
              {loading && <div className="text-xs text-gray-600">Loading...</div>}
              {!loading && proposals.length === 0 && (
                <div className="text-xs text-gray-600 text-center py-8">No pending proposals.</div>
              )}
              <div className="space-y-2 overflow-y-auto flex-1 pr-1">
                {proposals.map((p) => (
                  <div key={p.proposal_id} className="p-2.5 bg-black border border-gray-800 rounded space-y-1.5">
                    <div className="text-xs font-bold text-gray-200">{p.action_type}</div>
                    <div className="text-[10px] text-gray-500 break-all">{p.dataset_urn.split(',')[1]}</div>
                    <div className="text-[10px] text-gray-400">{p.description}</div>
                    <div className="flex gap-1.5 pt-1">
                      <button
                        onClick={() => handleApprove(p)}
                        disabled={applyingId === p.proposal_id}
                        className="flex-1 bg-emerald-950 hover:bg-emerald-900 disabled:opacity-50 border border-emerald-700 text-emerald-300 text-[10px] py-1 rounded font-bold transition-colors"
                      >
                        {applyingId === p.proposal_id ? '...' : 'APPROVE'}
                      </button>
                      <button
                        onClick={() => handleReject(p)}
                        disabled={applyingId === p.proposal_id}
                        className="flex-1 bg-red-950 hover:bg-red-900 disabled:opacity-50 border border-red-700 text-red-300 text-[10px] py-1 rounded font-bold transition-colors"
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
          <div className="bg-[#0a0a0f] border border-gray-800 rounded-lg p-4 shrink-0">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs text-gray-400 font-semibold tracking-wider uppercase">Live Metrics</h3>
              <div className="flex gap-3">
                {(Object.keys(METRIC_CONFIG) as MetricKey[]).map((key) => (
                  <div key={key} className="flex items-center gap-1.5 text-[10px]">
                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: METRIC_CONFIG[key].color }}></span>
                    <span className="text-gray-400">{METRIC_CONFIG[key].label}</span>
                  </div>
                ))}
              </div>
            </div>
            {history.quality.length === 0 ? (
              <div className="text-xs text-gray-600 text-center py-12">
                Collecting data... first point in a few seconds.
              </div>
            ) : (
              <CombinedMetricsChart history={history} />
            )}
          </div>

          {/* Quality Insights + PII Distribution */}
          <div className="grid grid-cols-2 gap-6 shrink-0">
            <div className="bg-[#0a0a0f] border border-gray-800 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-xs text-gray-400 font-semibold tracking-wider uppercase">Data Quality Insights</h3>
                <span className="text-2xl font-bold text-emerald-400">{loading ? '...' : quality?.overall_score ?? 0}</span>
              </div>
              {!loading && (quality?.top_issues.length ?? 0) === 0 && (
                <div className="text-xs text-gray-600">No active quality issues detected.</div>
              )}
              <div className="space-y-2">
                {quality?.top_issues.map((issue, i) => (
                  <div key={i} className="flex items-center justify-between text-xs border-b border-gray-900 pb-2">
                    <div>
                      <div className="text-gray-300">{issue.type}</div>
                      <div className="text-gray-600 text-[11px]">{issue.column}</div>
                    </div>
                    <span className="text-amber-400 font-bold shrink-0 ml-2">{issue.percentage}%</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-[#0a0a0f] border border-gray-800 rounded-lg p-4">
              <h3 className="text-xs text-gray-400 font-semibold tracking-wider uppercase mb-3">PII Distribution</h3>
              {!loading && piiDist && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-red-400">High Risk</span>
                    <span className="text-gray-300">{piiDist.high_risk} ({piiDist.high_pct}%)</span>
                  </div>
                  <div className="h-1.5 bg-gray-900 rounded-full overflow-hidden">
                    <div className="h-full bg-red-500" style={{ width: `${piiDist.high_pct}%` }}></div>
                  </div>

                  <div className="flex items-center justify-between text-xs">
                    <span className="text-amber-400">Medium Risk</span>
                    <span className="text-gray-300">{piiDist.medium_risk} ({piiDist.medium_pct}%)</span>
                  </div>
                  <div className="h-1.5 bg-gray-900 rounded-full overflow-hidden">
                    <div className="h-full bg-amber-500" style={{ width: `${piiDist.medium_pct}%` }}></div>
                  </div>

                  <div className="flex items-center justify-between text-xs">
                    <span className="text-emerald-400">Low Risk</span>
                    <span className="text-gray-300">{piiDist.low_risk} ({piiDist.low_pct}%)</span>
                  </div>
                  <div className="h-1.5 bg-gray-900 rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-500" style={{ width: `${piiDist.low_pct}%` }}></div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}