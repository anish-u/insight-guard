import React from "react";
import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import StatusPage from "./pages/StatusPage";
import WeeklyDhsPage from "./pages/WeeklyDhsPage";
import MonthlyDhsWebPage from "./pages/MonthlyDhsWebPage";
import DeptScanPage from "./pages/DeptScanPage";

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col">
        <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur">
          <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
            <div className="font-semibold text-slate-100">InsightGuard</div>
            <nav className="flex gap-4 text-sm">
              <NavLink
                to="/"
                className={({ isActive }) =>
                  isActive
                    ? "text-sky-400"
                    : "text-slate-300 hover:text-sky-300"
                }
                end
              >
                Status
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
                to="/monthly-dhs-web"
                className={({ isActive }) =>
                  isActive
                    ? "text-sky-400"
                    : "text-slate-300 hover:text-sky-300"
                }
              >
                Monthly DHS Web
              </NavLink>
              <NavLink
                to="/dept-scans"
                className={({ isActive }) =>
                  isActive
                    ? "text-sky-400"
                    : "text-slate-300 hover:text-sky-300"
                }
              >
                Departmental Scans
              </NavLink>
            </nav>
          </div>
        </header>

        <main className="flex-1 w-full max-w-5xl mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<StatusPage />} />
            <Route path="/weekly-dhs" element={<WeeklyDhsPage />} />
            <Route path="/monthly-dhs-web" element={<MonthlyDhsWebPage />} />
            <Route path="/dept-scans" element={<DeptScanPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
};

export default App;
