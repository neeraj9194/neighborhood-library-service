"use client";

import { useEffect, useState } from "react";
import StatsCard from "@/components/StatsCard";
import {
  fetchStats,
  fetchOverdue,
  type Stats,
  type BorrowRecord,
} from "@/lib/api";

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [overdue, setOverdue] = useState<BorrowRecord[]>([]);
  const [overdueTotal, setOverdueTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchStats(),
      fetchOverdue({ page: 1, size: 50 }),
    ])
      .then(([statsData, overdueData]) => {
        setStats(statsData);
        setOverdue(overdueData.items);
        setOverdueTotal(overdueData.total);
      })
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
            <h3 className="section-title">⏰ Overdue Books ({overdueTotal})</h3>
            {overdue.length === 0 ? (
              <p style={{ color: "var(--text-muted)", padding: "16px 0" }}>
                No overdue books — everything is on time! 🎉
              </p>
            ) : (
              <div className="data-table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Book</th>
                      <th>Member</th>
                      <th>Borrowed</th>
                      <th>Due Date</th>
                      <th>Days Overdue</th>
                    </tr>
                  </thead>
                  <tbody>
                    {overdue.map((r) => {
                      const daysOverdue = Math.floor(
                        (Date.now() - new Date(r.due_date).getTime()) / (1000 * 60 * 60 * 24)
                      );
                      return (
                        <tr key={r.id}>
                          <td style={{ fontWeight: 600 }}>{r.book_title || `Book #${r.book_id}`}</td>
                          <td>{r.member_name || `Member #${r.member_id}`}</td>
                          <td style={{ color: "var(--text-secondary)" }}>
                            {new Date(r.borrowed_at).toLocaleDateString()}
                          </td>
                          <td style={{ color: "var(--danger)" }}>
                            {new Date(r.due_date).toLocaleDateString()}
                          </td>
                          <td>
                            <span className="badge inactive">
                              <span className="badge-dot" />
                              {daysOverdue} day{daysOverdue !== 1 ? "s" : ""}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      ) : (
        <p style={{ color: "var(--text-muted)" }}>Failed to load stats.</p>
      )}
    </>
  );
}
