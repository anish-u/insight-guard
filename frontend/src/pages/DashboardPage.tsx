import React, { useEffect, useState } from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { RefreshCcw } from "lucide-react";
import GraphView, { GraphNode, GraphLink } from "../components/GraphView";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

type GraphSection = {
  loading: boolean;
  error: string | null;
  summary: Record<string, any> | null;
  nodes: GraphNode[];
  links: GraphLink[];
  meta: Record<string, any> | null;
};

const initialSection: GraphSection = {
  loading: false,
  error: null,
  summary: null,
  nodes: [],
  links: [],
  meta: null,
};

const DashboardPage: React.FC = () => {
  const [weekly, setWeekly] = useState<GraphSection>(initialSection);
  const [monthlyWeb, setMonthlyWeb] = useState<GraphSection>(initialSection);
  const [dept, setDept] = useState<GraphSection>(initialSection);

  const fetchWeekly = async () => {
    setWeekly((s) => ({ ...s, loading: true, error: null }));
    try {
      const res = await fetch(`${API_BASE_URL}/dashboard/weekly-latest`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setWeekly({
        loading: false,
        error: null,
        summary: data.summary,
        nodes: data.graph?.nodes || [],
        links: data.graph?.links || [],
        meta: {
          scan_id: data.scan_id,
          year: data.year,
          month: data.month,
          week_index: data.week_index,
        },
      });
    } catch (e: any) {
      setWeekly((s) => ({
        ...s,
        loading: false,
        error: e.message || "Failed to load weekly dashboard",
      }));
    }
  };

  const fetchMonthlyWeb = async () => {
    setMonthlyWeb((s) => ({ ...s, loading: true, error: null }));
    try {
      const res = await fetch(`${API_BASE_URL}/dashboard/monthly-web-latest`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setMonthlyWeb({
        loading: false,
        error: null,
        summary: data.summary,
        nodes: data.graph?.nodes || [],
        links: data.graph?.links || [],
        meta: {
          scan_id: data.scan_id,
          year: data.year,
          month: data.month,
        },
      });
    } catch (e: any) {
      setMonthlyWeb((s) => ({
        ...s,
        loading: false,
        error: e.message || "Failed to load monthly web dashboard",
      }));
    }
  };

  const fetchDept = async () => {
    // default department IT; you can make this a dropdown later
    const deptName = "IT";
    setDept((s) => ({ ...s, loading: true, error: null }));
    try {
      const res = await fetch(
        `${API_BASE_URL}/dashboard/dept-latest?department=${encodeURIComponent(
          deptName
        )}`
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setDept({
        loading: false,
        error: null,
        summary: data.summary,
        nodes: data.graph?.nodes || [],
        links: data.graph?.links || [],
        meta: {
          scan_id: data.scan_id,
          year: data.year,
          month: data.month,
          department: data.department,
        },
      });
    } catch (e: any) {
      setDept((s) => ({
        ...s,
        loading: false,
        error: e.message || "Failed to load departmental dashboard",
      }));
    }
  };

  // load all on mount
  useEffect(() => {
    fetchWeekly();
    fetchMonthlyWeb();
    fetchDept();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const renderSummary = (summary: Record<string, any> | null) => {
    if (!summary) return null;
    return (
      <dl className="grid grid-cols-2 gap-3 mt-3 text-xs text-slate-300">
        {Object.entries(summary).map(([key, value]) => (
          <div key={key}>
            <dt className="uppercase tracking-wide text-[0.6rem] text-slate-500">
              {key.replace(/_/g, " ")}
            </dt>
            <dd className="font-semibold text-slate-100">{String(value)}</dd>
          </div>
        ))}
      </dl>
    );
  };

  const renderMetaLine = (meta: Record<string, any> | null) => {
    if (!meta) return null;
    return (
      <p className="text-xs text-slate-400">
        {Object.entries(meta)
          .map(([k, v]) => `${k}: ${v}`)
          .join(" · ")}
      </p>
    );
  };

  return (
    <div className="space-y-6">
      <header className="mb-2">
        <h1 className="text-2xl font-bold mb-1">Security Graph Dashboard</h1>
        <p className="text-sm text-slate-400">
          Live view of the latest Weekly DHS, Monthly DHS Web, and Departmental
          scans as graph structures.
        </p>
      </header>

      <section className="grid gap-6 lg:grid-cols-2">
        {/* Weekly DHS */}
        <Card className="col-span-1">
          <CardHeader className="flex items-center justify-between">
            <div>
              <CardTitle>Weekly DHS (Latest)</CardTitle>
              {renderMetaLine(weekly.meta)}
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchWeekly}
              disabled={weekly.loading}
            >
              <RefreshCcw className="w-4 h-4 mr-1" />
              {weekly.loading ? "Refreshing..." : "Refresh"}
            </Button>
          </CardHeader>
          <CardContent>
            {weekly.error && (
              <p className="text-xs text-red-300 mb-2">{weekly.error}</p>
            )}
            <GraphView nodes={weekly.nodes} links={weekly.links} />
            {renderSummary(weekly.summary)}
          </CardContent>
        </Card>

        {/* Monthly Web */}
        <Card className="col-span-1">
          <CardHeader className="flex items-center justify-between">
            <div>
              <CardTitle>Monthly DHS Web (Latest)</CardTitle>
              {renderMetaLine(monthlyWeb.meta)}
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchMonthlyWeb}
              disabled={monthlyWeb.loading}
            >
              <RefreshCcw className="w-4 h-4 mr-1" />
              {monthlyWeb.loading ? "Refreshing..." : "Refresh"}
            </Button>
          </CardHeader>
          <CardContent>
            {monthlyWeb.error && (
              <p className="text-xs text-red-300 mb-2">{monthlyWeb.error}</p>
            )}
            <GraphView nodes={monthlyWeb.nodes} links={monthlyWeb.links} />
            {renderSummary(monthlyWeb.summary)}
          </CardContent>
        </Card>

        {/* Dept */}
        <Card className="col-span-1 lg:col-span-2">
          <CardHeader className="flex items-center justify-between">
            <div>
              <CardTitle>Departmental Scan (Latest, IT)</CardTitle>
              {renderMetaLine(dept.meta)}
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchDept}
              disabled={dept.loading}
            >
              <RefreshCcw className="w-4 h-4 mr-1" />
              {dept.loading ? "Refreshing..." : "Refresh"}
            </Button>
          </CardHeader>
          <CardContent>
            {dept.error && (
              <p className="text-xs text-red-300 mb-2">{dept.error}</p>
            )}
            <GraphView nodes={dept.nodes} links={dept.links} height={360} />
            {renderSummary(dept.summary)}
          </CardContent>
        </Card>
      </section>
    </div>
  );
};

export default DashboardPage;
