import React, { useEffect, useState } from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { RefreshCcw } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  Legend,
} from "recharts";
import GraphView, { GraphNode, GraphLink } from "../components/GraphView";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

type WeeklyScan = {
  scan_id: string;
  year?: number;
  month?: number;
  week_index?: number;
  scan_date?: string;
};

type WeeklySummary = {
  total_observations: number;
  critical: number;
  high: number;
  host_count: number;
  vuln_count: number;
  known_exploited_count: number;
  ransomware_exploited_count: number;
};

type SeverityBucket = { severity: number; count: number };
type TopHost = {
  ip: string;
  hostname?: string;
  findings: number;
  critical: number;
};
type TopVuln = {
  weekly_vuln_id: string;
  plugin_id?: number;
  name?: string;
  severity?: number;
  cvss?: number;
  known_exploited: boolean;
  ransomware_exploited: boolean;
  findings: number;
};

type ChartsData = {
  severity_buckets: SeverityBucket[];
  top_hosts: TopHost[];
  top_vulns: TopVuln[];
};

type Finding = {
  obs_id: string;
  severity: number;
  cvss?: number;
  first_seen?: string;
  last_seen?: string;
  age_days?: number;
  ip: string;
  hostname?: string;
  plugin_id?: number;
  vuln_name?: string;
  known_exploited: boolean;
  ransomware_exploited: boolean;
};

type FindingsResponse = {
  total: number;
  items: Finding[];
  offset: number;
  limit: number;
};

type GraphResponse = {
  summary: {
    observation_count: number;
    host_count: number;
    vuln_count: number;
    node_count: number;
    link_count: number;
  };
  graph: {
    nodes: GraphNode[];
    links: GraphLink[];
  };
};

const WeeklyDhsPage: React.FC = () => {
  const [scans, setScans] = useState<WeeklyScan[]>([]);
  const [selectedScanId, setSelectedScanId] = useState<string | null>(null);

  const [summary, setSummary] = useState<WeeklySummary | null>(null);
  const [charts, setCharts] = useState<ChartsData | null>(null);
  const [findings, setFindings] = useState<FindingsResponse | null>(null);
  const [graph, setGraph] = useState<GraphResponse | null>(null);

  const [minSeverity, setMinSeverity] = useState<number | null>(null);
  const [search, setSearch] = useState<string>("");
  const [page, setPage] = useState<number>(0);
  const pageSize = 10;

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadScans = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/weekly-dhs/scans`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setScans(data.items || []);
      if (!selectedScanId && data.items && data.items.length > 0) {
        setSelectedScanId(data.items[0].scan_id);
      }
    } catch (e: any) {
      console.error(e);
    }
  };

  const loadAllForScan = async (scanId: string, resetPage = true) => {
    setLoading(true);
    setError(null);
    try {
      // summary
      const [summaryRes, chartsRes, findingsRes, graphRes] = await Promise.all([
        fetch(`${API_BASE_URL}/weekly-dhs/${scanId}/summary`),
        fetch(
          `${API_BASE_URL}/weekly-dhs/${scanId}/charts?` +
            new URLSearchParams(
              minSeverity ? { min_severity: String(minSeverity) } : {}
            )
        ),
        fetch(
          `${API_BASE_URL}/weekly-dhs/${scanId}/findings?` +
            new URLSearchParams({
              ...(minSeverity ? { min_severity: String(minSeverity) } : {}),
              ...(search ? { search } : {}),
              offset: String((resetPage ? 0 : page) * pageSize),
              limit: String(pageSize),
            })
        ),
        fetch(`${API_BASE_URL}/weekly-dhs/${scanId}/graph`),
      ]);

      if (!summaryRes.ok) throw new Error("Failed to load summary");
      if (!chartsRes.ok) throw new Error("Failed to load charts");
      if (!findingsRes.ok) throw new Error("Failed to load findings");
      if (!graphRes.ok) throw new Error("Failed to load graph");

      const summaryData = await summaryRes.json();
      const chartsData = await chartsRes.json();
      const findingsData = await findingsRes.json();
      const graphData = await graphRes.json();

      setSummary(summaryData.summary);
      setCharts(chartsData);
      setFindings(findingsData);
      setGraph(graphData);
      if (resetPage) setPage(0);
    } catch (e: any) {
      console.error(e);
      setError(e.message || "Failed to load Weekly DHS data");
    } finally {
      setLoading(false);
    }
  };

  // initial scans load
  useEffect(() => {
    loadScans();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // whenever selected scan or filters change, reload
  useEffect(() => {
    if (!selectedScanId) return;
    loadAllForScan(selectedScanId, true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedScanId, minSeverity]);

  // page changes (without resetting other filters)
  useEffect(() => {
    if (!selectedScanId) return;
    loadAllForScan(selectedScanId, false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  const selectedScan = scans.find((s) => s.scan_id === selectedScanId) || null;

  const totalPages = findings
    ? Math.max(1, Math.ceil(findings.total / pageSize))
    : 1;

  const severityOptions = [
    { label: "All severities", value: null },
    { label: "Severity ≥ 3", value: 3 },
    { label: "Severity ≥ 4", value: 4 },
    { label: "Only 5 (Critical)", value: 5 },
  ];

  const formatScanLabel = (scan: WeeklyScan) =>
    `${scan.scan_id} (${scan.year}-${String(scan.month).padStart(2, "0")} wk${
      scan.week_index
    })`;

  return (
    <div className="space-y-6">
      <header className="mb-2 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-bold mb-1">Weekly DHS – Analytics</h1>
          <p className="text-sm text-slate-400">
            Explore findings, hosts, and vulnerabilities for individual Weekly
            DHS scans.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Scan selector */}
          <div className="flex flex-col">
            <label className="text-xs text-slate-400 mb-1">Select scan</label>
            <select
              className="bg-slate-900 text-sm rounded-md border border-slate-700 px-2 py-1"
              value={selectedScanId || ""}
              onChange={(e) => setSelectedScanId(e.target.value || null)}
            >
              {scans.map((scan) => (
                <option key={scan.scan_id} value={scan.scan_id}>
                  {formatScanLabel(scan)}
                </option>
              ))}
            </select>
          </div>

          {/* Severity filter */}
          <div className="flex flex-col">
            <label className="text-xs text-slate-400 mb-1">Min severity</label>
            <select
              className="bg-slate-900 text-sm rounded-md border border-slate-700 px-2 py-1"
              value={minSeverity ?? ""}
              onChange={(e) =>
                setMinSeverity(
                  e.target.value === "" ? null : Number(e.target.value)
                )
              }
            >
              {severityOptions.map((opt) => (
                <option
                  key={opt.label}
                  value={opt.value === null ? "" : opt.value}
                >
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Search */}
          <div className="flex flex-col">
            <label className="text-xs text-slate-400 mb-1">
              Search (IP / host / vuln)
            </label>
            <div className="flex gap-2">
              <input
                className="bg-slate-900 text-sm rounded-md border border-slate-700 px-2 py-1"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="e.g. 10.0.0.1 or TLS"
              />
              <Button
                variant="outline"
                onClick={() => {
                  if (selectedScanId) {
                    setPage(0);
                    loadAllForScan(selectedScanId, true);
                  }
                }}
              >
                <RefreshCcw className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      {selectedScan && (
        <p className="text-xs text-slate-500">
          scan_id:{" "}
          <span className="text-slate-200">{selectedScan.scan_id}</span> · year:{" "}
          {selectedScan.year} · month: {selectedScan.month} · week:{" "}
          {selectedScan.week_index}
        </p>
      )}

      {error && (
        <p className="text-xs text-red-300 bg-red-950/40 border border-red-700 rounded-md px-3 py-2">
          {error}
        </p>
      )}

      {/* KPI cards */}
      <section className="grid gap-4 md:grid-cols-3 lg:grid-cols-6">
        <KpiCard
          label="Total Findings"
          value={summary?.total_observations ?? 0}
        />
        <KpiCard label="Critical (5)" value={summary?.critical ?? 0} />
        <KpiCard label="High (4)" value={summary?.high ?? 0} />
        <KpiCard label="Hosts" value={summary?.host_count ?? 0} />
        <KpiCard label="Distinct Vulns" value={summary?.vuln_count ?? 0} />
        <KpiCard
          label="Known Exploited"
          value={summary?.known_exploited_count ?? 0}
        />
      </section>

      {/* Charts row */}
      <section className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Severity distribution</CardTitle>
          </CardHeader>
          <CardContent className="h-64">
            {charts && charts.severity_buckets.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={charts.severity_buckets}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="severity" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#020617",
                      borderColor: "#1e293b",
                      fontSize: 12,
                    }}
                  />
                  <Bar dataKey="count" fill="#38bdf8" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-xs text-slate-500">
                No severity data available.
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Top hosts by findings</CardTitle>
          </CardHeader>
          <CardContent className="h-64">
            {charts && charts.top_hosts.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={charts.top_hosts}
                  layout="vertical"
                  margin={{ left: 60, right: 16, top: 16, bottom: 16 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis type="number" stroke="#94a3b8" />
                  <YAxis
                    dataKey="ip"
                    type="category"
                    stroke="#94a3b8"
                    tickFormatter={(ip) => String(ip)}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#020617",
                      borderColor: "#1e293b",
                      fontSize: 12,
                    }}
                  />
                  <Legend />
                  <Bar dataKey="findings" name="Findings" fill="#4ade80" />
                  <Bar dataKey="critical" name="Critical" fill="#f97316" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-xs text-slate-500">No host data available.</p>
            )}
          </CardContent>
        </Card>
      </section>

      {/* Top vulns & graph */}
      <section className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Top vulnerabilities</CardTitle>
          </CardHeader>
          <CardContent className="h-72">
            {charts && charts.top_vulns.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={charts.top_vulns}
                  margin={{ left: 40, right: 16, top: 16, bottom: 80 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis
                    dataKey="name"
                    stroke="#94a3b8"
                    angle={-30}
                    textAnchor="end"
                    interval={0}
                  />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#020617",
                      borderColor: "#1e293b",
                      fontSize: 12,
                    }}
                  />
                  <Bar dataKey="findings" name="Findings" fill="#fbbf24" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-xs text-slate-500">
                No vulnerability data available.
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Graph view (sample)</CardTitle>
          </CardHeader>
          <CardContent>
            {graph ? (
              <>
                <GraphView
                  nodes={graph.graph.nodes}
                  links={graph.graph.links}
                  height={320}
                />
                <p className="mt-3 text-xs text-slate-500">
                  nodes: {graph.summary.node_count} · links:{" "}
                  {graph.summary.link_count} · hosts: {graph.summary.host_count}{" "}
                  · vulns: {graph.summary.vuln_count}
                </p>
              </>
            ) : (
              <p className="text-xs text-slate-500">No graph data available.</p>
            )}
          </CardContent>
        </Card>
      </section>

      {/* Findings table */}
      <Card>
        <CardHeader>
          <CardTitle>Findings table</CardTitle>
        </CardHeader>
        <CardContent>
          {findings && findings.items.length > 0 ? (
            <>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 bg-slate-900/40">
                      <th className="px-2 py-2">Severity</th>
                      <th className="px-2 py-2">Host</th>
                      <th className="px-2 py-2">Vulnerability</th>
                      <th className="px-2 py-2">Plugin ID</th>
                      <th className="px-2 py-2">CVSS</th>
                      <th className="px-2 py-2">Known Exploited</th>
                      <th className="px-2 py-2">Ransomware</th>
                      <th className="px-2 py-2">Age (days)</th>
                      <th className="px-2 py-2">First seen</th>
                      <th className="px-2 py-2">Last seen</th>
                    </tr>
                  </thead>
                  <tbody>
                    {findings.items.map((f) => {
                      return (
                        <tr
                          key={f.obs_id}
                          className="border-b border-slate-900/60 hover:bg-slate-900/60"
                        >
                          <td className="px-2 py-1 font-semibold">
                            {f.severity}
                          </td>
                          <td className="px-2 py-1">
                            <div className="flex flex-col">
                              <span className="text-slate-100">{f.ip}</span>
                              {f.hostname && (
                                <span className="text-slate-400">
                                  {f.hostname}
                                </span>
                              )}
                            </div>
                          </td>
                          <td className="px-2 py-1 max-w-xs">
                            <span className="line-clamp-2">
                              {f.vuln_name || "-"}
                            </span>
                          </td>
                          <td className="px-2 py-1">{f.plugin_id ?? "-"}</td>
                          <td className="px-2 py-1">
                            {f.cvss != null ? f.cvss.toFixed(1) : "-"}
                          </td>
                          <td className="px-2 py-1">
                            {f.known_exploited ? "Yes" : "No"}
                          </td>
                          <td className="px-2 py-1">
                            {f.ransomware_exploited ? "Yes" : "No"}
                          </td>
                          <td className="px-2 py-1">{f.age_days ?? "-"}</td>
                          <td className="px-2 py-1 text-slate-400">
                            {f.first_seen ? String(f.first_seen) : "-"}
                          </td>
                          <td className="px-2 py-1 text-slate-400">
                            {f.last_seen ? String(f.last_seen) : "-"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              <div className="flex items-center justify-between mt-3 text-xs text-slate-400">
                <span>
                  Showing {findings.offset + 1}–
                  {Math.min(
                    findings.offset + findings.items.length,
                    findings.total
                  )}{" "}
                  of {findings.total}
                </span>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    disabled={page === 0}
                    onClick={() => setPage((p) => Math.max(0, p - 1))}
                  >
                    Prev
                  </Button>
                  <span>
                    Page {page + 1} / {totalPages}
                  </span>
                  <Button
                    variant="outline"
                    disabled={page + 1 >= totalPages}
                    onClick={() => setPage((p) => p + 1)}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <p className="text-xs text-slate-500">
              No findings to display. Try changing filters or upload a Weekly
              DHS report.
            </p>
          )}
        </CardContent>
      </Card>

      {loading && (
        <p className="text-xs text-slate-400">Loading Weekly DHS data…</p>
      )}
    </div>
  );
};

type KpiCardProps = {
  label: string;
  value: number;
};

const KpiCard: React.FC<KpiCardProps> = ({ label, value }) => (
  <Card>
    <CardContent className="py-3">
      <div className="text-[0.7rem] uppercase tracking-wide text-slate-500">
        {label}
      </div>
      <div className="text-xl font-semibold text-slate-100 mt-1">
        {value.toLocaleString()}
      </div>
    </CardContent>
  </Card>
);

export default WeeklyDhsPage;
