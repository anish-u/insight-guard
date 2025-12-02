import React, { useState } from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { UploadCloud } from "lucide-react";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const months = [
  { value: 1, label: "January" },
  { value: 2, label: "February" },
  { value: 3, label: "March" },
  { value: 4, label: "April" },
  { value: 5, label: "May" },
  { value: 6, label: "June" },
  { value: 7, label: "July" },
  { value: 8, label: "August" },
  { value: 9, label: "September" },
  { value: 10, label: "October" },
  { value: 11, label: "November" },
  { value: 12, label: "December" },
];

const WeeklyDhsPage: React.FC = () => {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [weekIndex, setWeekIndex] = useState(1);
  const [file, setFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a CSV file.");
      return;
    }
    setError(null);
    setResult(null);
    setSubmitting(true);

    try {
      const formData = new FormData();
      formData.append("year", year.toString());
      formData.append("month", month.toString());
      formData.append("week_index", weekIndex.toString());
      formData.append("report", file);

      const res = await fetch(`${API_BASE_URL}/ingest/weekly-dhs`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(`HTTP ${res.status}: ${text}`);
      }

      const data = await res.json();
      setResult(data);
    } catch (e: any) {
      setError(e.message || "Upload failed.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="w-full max-w-xl mx-auto">
      <Card>
        <CardHeader>
          <CardTitle>Weekly DHS Report Upload</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Scan Month
                </label>
                <select
                  className="w-full bg-slate-900 border border-slate-700 rounded-md px-3 py-2 text-sm"
                  value={month}
                  onChange={(e) => setMonth(Number(e.target.value))}
                >
                  {months.map((m) => (
                    <option key={m.value} value={m.value}>
                      {m.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Scan Year
                </label>
                <input
                  type="number"
                  className="w-full bg-slate-900 border border-slate-700 rounded-md px-3 py-2 text-sm"
                  value={year}
                  onChange={(e) => setYear(Number(e.target.value))}
                  min={2000}
                  max={2100}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Week in Month
                </label>
                <select
                  className="w-full bg-slate-900 border border-slate-700 rounded-md px-3 py-2 text-sm"
                  value={weekIndex}
                  onChange={(e) => setWeekIndex(Number(e.target.value))}
                >
                  {[1, 2, 3, 4, 5].map((w) => (
                    <option key={w} value={w}>
                      Week {w}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Weekly DHS CSV
              </label>
              <input
                type="file"
                accept=".csv"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="block w-full text-xs text-slate-300 file:mr-3 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-xs file:font-medium file:bg-sky-600 file:text-white hover:file:bg-sky-700"
              />
            </div>

            <Button
              type="submit"
              disabled={submitting || !file}
              className="mt-2"
            >
              <UploadCloud className="w-4 h-4 mr-2" />
              {submitting ? "Uploading..." : "Upload & Ingest"}
            </Button>
          </form>

          {result && (
            <div className="mt-4 text-xs text-emerald-300 space-y-1">
              <div>Upload successful.</div>
              <div>Scan ID: {result.scan_id}</div>
              <div>
                Month/Year: {result.month}/{result.year}, Week{" "}
                {result.week_index}
              </div>
              <div>Stored at: {result.stored_at}</div>
            </div>
          )}

          {error && (
            <div className="mt-4 text-xs text-red-300">Error: {error}</div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default WeeklyDhsPage;
