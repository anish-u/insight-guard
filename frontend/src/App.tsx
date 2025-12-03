import React from "react";
import { BrowserRouter, Routes, Route, NavLink, Link } from "react-router-dom";
import WeeklyDhsUploadPage from "./pages/WeeklyDhsUploadPage";
import WeeklyDhsPage from "./pages/WeeklyDhsPage";
import MonthlyDhsWebUploadPage from "./pages/MonthlyDhsWebUploadPage";
import DeptScanUploadPage from "./pages/DeptScanUploadPage";
import DashboardPage from "./pages/DashboardPage";

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col">
        <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur">
          <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
            <div className="font-semibold text-slate-100">
              <Link to="/">InsightGuard</Link>
            </div>
            <nav className="flex gap-4 text-sm">
              <NavLink
                to="/dashboard"
                className={({ isActive }) =>
                  isActive
                    ? "text-sky-400"
                    : "text-slate-300 hover:text-sky-300"
                }
              >
                Dashboard
              </NavLink>
              <NavLink
                to="/weekly-dhs"
                className={({ isActive }) =>
                  isActive
                    ? "text-sky-400"
                    : "text-slate-300 hover:text-sky-300"
                }
              >
                Weekly DHS
              </NavLink>
              <NavLink
                to="/weekly-dhs-upload"
                className={({ isActive }) =>
                  isActive
                    ? "text-sky-400"
                    : "text-slate-300 hover:text-sky-300"
                }
              >
                Upload Weekly DHS
              </NavLink>
              <NavLink
                to="/monthly-dhs-web-upload"
                className={({ isActive }) =>
                  isActive
                    ? "text-sky-400"
                    : "text-slate-300 hover:text-sky-300"
                }
              >
                Upload Monthly DHS Web
              </NavLink>
              <NavLink
                to="/dept-scans-upload"
                className={({ isActive }) =>
                  isActive
                    ? "text-sky-400"
                    : "text-slate-300 hover:text-sky-300"
                }
              >
                Upload Departmental Scans
              </NavLink>
            </nav>
          </div>
        </header>

        <main className="flex-1 w-full max-w-5xl mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route
              path="/weekly-dhs-upload"
              element={<WeeklyDhsUploadPage />}
            />
            <Route path="/weekly-dhs" element={<WeeklyDhsPage />} />
            <Route
              path="/monthly-dhs-web-upload"
              element={<MonthlyDhsWebUploadPage />}
            />
            <Route path="/dept-scans-upload" element={<DeptScanUploadPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
};

export default App;
