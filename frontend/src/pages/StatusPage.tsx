import React, { useState } from "react";
import { Button } from "../components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "../components/ui/card";
import { RefreshCcw, HeartPulse } from "lucide-react";

type HealthResponse = {
  status: string;
  neo4j?: string;
};

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const StatusPage: React.FC = () => {
  const [hello, setHello] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loadingHello, setLoadingHello] = useState(false);
  const [loadingHealth, setLoadingHealth] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchHello = async () => {
    setLoadingHello(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/hello`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setHello(data.message ?? JSON.stringify(data));
    } catch (e: any) {
      setError(`Failed to fetch /hello: ${e.message}`);
    } finally {
      setLoadingHello(false);
    }
  };

  const fetchHealth = async () => {
    setLoadingHealth(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/health`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = (await res.json()) as HealthResponse;
      setHealth(data);
    } catch (e: any) {
      setError(`Failed to fetch /health: ${e.message}`);
    } finally {
      setLoadingHealth(false);
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto">
      <header className="mb-8">
        <h1 className="text-2xl font-bold mb-1">System Status</h1>
        <p className="text-sm text-slate-400">
          Check connectivity between frontend, backend, and Neo4j.
        </p>
      </header>

      <main className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader className="flex items-center justify-between">
            <CardTitle>/hello</CardTitle>
            <Button
              variant="outline"
              onClick={fetchHello}
              disabled={loadingHello}
            >
              <RefreshCcw className="w-4 h-4 mr-2" />
              {loadingHello ? "Loading..." : "Call"}
            </Button>
          </CardHeader>
          <CardContent>
            {hello ? (
              <p className="text-sm text-slate-100">{hello}</p>
            ) : (
              <p className="text-sm text-slate-500">
                Click &quot;Call&quot; to hit the <code>/hello</code> endpoint.
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex items-center justify-between">
            <CardTitle>/health</CardTitle>
            <Button
              variant="outline"
              onClick={fetchHealth}
              disabled={loadingHealth}
            >
              <HeartPulse className="w-4 h-4 mr-2" />
              {loadingHealth ? "Checking..." : "Check"}
            </Button>
          </CardHeader>
          <CardContent>
            {health ? (
              <div className="space-y-1 text-sm">
                <div>
                  <span className="font-medium text-slate-200">Status: </span>
                  <span
                    className={
                      health.status === "ok"
                        ? "text-emerald-400"
                        : "text-amber-400"
                    }
                  >
                    {health.status}
                  </span>
                </div>
                {health.neo4j && (
                  <div>
                    <span className="font-medium text-slate-200">
                      Neo4j:&nbsp;
                    </span>
                    <span className="text-slate-300">{health.neo4j}</span>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-slate-500">
                Click &quot;Check&quot; to verify API ↔ Neo4j connectivity.
              </p>
            )}
          </CardContent>
        </Card>
      </main>

      {error && (
        <div className="mt-6">
          <Card className="border-red-900 bg-red-950/60">
            <CardHeader>
              <CardTitle className="text-red-400 text-sm">Error</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-red-200">{error}</p>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default StatusPage;
