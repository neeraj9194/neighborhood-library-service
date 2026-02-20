"use client";

import { useEffect, useState } from "react";
import StatsCard from "@/components/StatsCard";
import { fetchStats, type Stats } from "@/lib/api";

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats()
      .then(setStats)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      <div className="page-header">
        <h2>Dashboard</h2>
        <p>Overview of your neighborhood library</p>
      </div>

      {loading ? (
        <div className="stats-grid">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="loading-skeleton" style={{ height: 140 }} />
          ))}
        </div>
      ) : stats ? (
        <div>
          <div className="dashboard-section">
            <h3 className="section-title">Books Overview</h3>
            <div className="stats-grid">
              <StatsCard icon="📚" value={stats.total_books} label="Total Books" variant="accent" />
              <StatsCard icon="📦" value={stats.total_copies} label="Total Copies" variant="info" />
              <StatsCard icon="📖" value={stats.borrowed_copies} label="Borrowed Copies" variant="warning" />
              <StatsCard icon="✅" value={stats.available_copies} label="Available Copies" variant="success" />
            </div>
          </div>

          <div className="dashboard-section">
            <h3 className="section-title">Members Overview</h3>
            <div className="stats-grid">
              <StatsCard icon="👥" value={stats.total_members} label="Total Members" variant="accent" />
              <StatsCard icon="🟢" value={stats.active_members} label="Active Members" variant="success" />
            </div>
          </div>

          <div className="dashboard-section">
            <h3 className="section-title">Alerts</h3>
            <div className="stats-grid">
              <StatsCard icon="⏰" value={stats.overdue_count} label="Overdue" variant="danger" />
            </div>
          </div>
        </div>
        // <div className="stats-grid">
        //   <StatsCard icon="📚" value={stats.total_books} label="Total Books" variant="accent" />
        //   <StatsCard icon="📦" value={stats.total_copies} label="Total Copies of Books" variant="info" />
        //   <StatsCard icon="📖" value={stats.borrowed_copies} label="Borrowed Copies" variant="warning" />
        //   <StatsCard icon="✅" value={stats.available_copies} label="Available Copies" variant="success" />
        //   <StatsCard icon="👥" value={stats.total_members} label="Total Members" variant="accent" />
        //   <StatsCard icon="🟢" value={stats.active_members} label="Active Members" variant="success" />
        //   <StatsCard icon="⏰" value={stats.overdue_count} label="Overdue" variant="danger" />
        // </div>
      ) : (
        <p style={{ color: "var(--text-muted)" }}>Failed to load stats.</p>
      )}
    </>
  );
}
