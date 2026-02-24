"use client";

import { useEffect, useState } from "react";
import StatsCard from "@/components/StatsCard";
import DataTable, { type Column } from "@/components/DataTable";
import Toast from "@/components/Toast";
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
  const [error, setError] = useState<string | null>(null);

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
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load dashboard data");
      })
      .finally(() => setLoading(false));
  }, []);

  const overdueColumns: Column<BorrowRecord>[] = [
    {
      key: "book_title",
      header: "Book",
      className: "font-semibold",
      render: (r) => r.book_title || `Book #${r.book_id}`,
    },
    {
      key: "member_name",
      header: "Member",
      render: (r) => r.member_name || `Member #${r.member_id}`,
    },
    {
      key: "borrowed_at",
      header: "Borrowed",
      className: "text-secondary",
      render: (r) => new Date(r.borrowed_at).toLocaleDateString(),
    },
    {
      key: "due_date",
      header: "Due Date",
      className: "text-danger",
      render: (r) => new Date(r.due_date).toLocaleDateString(),
    },
    {
      key: "days_overdue",
      header: "Days Overdue",
      render: (r) => {
        const days = Math.floor(
          (Date.now() - new Date(r.due_date).getTime()) / (1000 * 60 * 60 * 24)
        );
        return (
          <span className="badge inactive">
            <span className="badge-dot" />
            {days} day{days !== 1 ? "s" : ""}
          </span>
        );
      },
    },
  ];

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
      ) : error ? (
        <div className="inline-alert error">{error}</div>
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
              <p className="empty-state">
                No overdue books — everything is on time! 🎉
              </p>
            ) : (
              <DataTable
                columns={overdueColumns}
                data={overdue}
                rowKey={(r) => r.id}
              />
            )}
          </div>
        </div>
      ) : (
        <p className="text-muted">Failed to load stats.</p>
      )}

      {error && <Toast type="error" message={error} />}
    </>
  );
}
