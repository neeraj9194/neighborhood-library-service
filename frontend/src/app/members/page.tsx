"use client";

import { useEffect, useState, useCallback } from "react";
import {
  fetchMembers,
  createMember,
  deactivateMember,
  type Member,
} from "@/lib/api";

export default function MembersPage() {
  const [members, setMembers] = useState<Member[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const size = 20;

  // Modal state
  const [showModal, setShowModal] = useState(false);
  const [formName, setFormName] = useState("");
  const [formEmail, setFormEmail] = useState("");
  const [formPhone, setFormPhone] = useState("");
  const [formAddress, setFormAddress] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Toast state
  const [toast, setToast] = useState<{ type: "success" | "error"; message: string } | null>(null);

  const showToast = (type: "success" | "error", message: string) => {
    setToast({ type, message });
    setTimeout(() => setToast(null), 4000);
  };

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetchMembers({ page, size, search: search || undefined });
      setMembers(res.items);
      setTotal(res.total);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [page, search]);

  useEffect(() => {
    load();
  }, [load]);

  // Debounced search
  const [searchInput, setSearchInput] = useState("");
  useEffect(() => {
    const id = setTimeout(() => {
      setSearch(searchInput);
      setPage(1);
    }, 400);
    return () => clearTimeout(id);
  }, [searchInput]);

  const totalPages = Math.ceil(total / size);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formName || !formEmail) return;
    setSubmitting(true);
    try {
      await createMember({
        name: formName,
        email: formEmail,
        phone: formPhone || undefined,
        address: formAddress || undefined,
      });
      showToast("success", `Member "${formName}" registered successfully!`);
      setShowModal(false);
      setFormName("");
      setFormEmail("");
      setFormPhone("");
      setFormAddress("");
      load();
    } catch (err: unknown) {
      showToast("error", err instanceof Error ? err.message : "Registration failed");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeactivate = async (member: Member) => {
    if (!confirm(`Deactivate "${member.name}"? They will no longer be able to borrow books.`)) return;
    try {
      await deactivateMember(member.id);
      showToast("success", `"${member.name}" has been deactivated.`);
      load();
    } catch (err: unknown) {
      showToast("error", err instanceof Error ? err.message : "Deactivation failed");
    }
  };

  return (
    <>
      <div className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h2>Members</h2>
          <p>Manage library members and registrations</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>
          + Register Member
        </button>
      </div>

      {/* Search */}
      <div className="search-bar">
        <div className="search-input">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8" />
            <path d="M21 21l-4.35-4.35" />
          </svg>
          <input
            type="text"
            placeholder="Search by name or email..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div className="loading-skeleton" style={{ height: 400 }} />
      ) : members.length === 0 ? (
        <p style={{ color: "var(--text-muted)", textAlign: "center", padding: 40 }}>
          No members found{search ? ` matching "${search}"` : ""}.
        </p>
      ) : (
        <>
          <div className="data-table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Member</th>
                  <th>Email</th>
                  <th>Phone</th>
                  <th>Status</th>
                  <th>Joined</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {members.map((m) => (
                  <tr key={m.id}>
                    <td style={{ color: "var(--text-muted)" }}>#{m.id}</td>
                    <td style={{ fontWeight: 600 }}>{m.name}</td>
                    <td>{m.email}</td>
                    <td style={{ color: "var(--text-secondary)" }}>{m.phone || "—"}</td>
                    <td>
                      <span className={`badge ${m.is_active ? "active" : "inactive"}`}>
                        <span className="badge-dot" />
                        {m.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td style={{ color: "var(--text-secondary)" }}>
                      {new Date(m.created_at).toLocaleDateString()}
                    </td>
                    <td>
                      {m.is_active && (
                        <button
                          className="btn btn-danger btn-sm"
                          onClick={() => handleDeactivate(m)}
                        >
                          Deactivate
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="pagination">
              <button className="btn btn-secondary" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                Previous
              </button>
              <span className="pagination-info">
                Page {page} of {totalPages} ({total} members)
              </span>
              <button className="btn btn-secondary" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
                Next
              </button>
            </div>
          )}
        </>
      )}

      {/* Register Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Register New Member</h3>
            <form onSubmit={handleRegister}>
              <div className="borrow-form">
                <div className="form-group">
                  <label htmlFor="reg-name">Full Name *</label>
                  <input
                    id="reg-name"
                    type="text"
                    required
                    placeholder="John Doe"
                    value={formName}
                    onChange={(e) => setFormName(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="reg-email">Email Address *</label>
                  <input
                    id="reg-email"
                    type="email"
                    required
                    placeholder="john@example.com"
                    value={formEmail}
                    onChange={(e) => setFormEmail(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="reg-phone">Phone</label>
                  <input
                    id="reg-phone"
                    type="tel"
                    placeholder="+1 555-0100"
                    value={formPhone}
                    onChange={(e) => setFormPhone(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="reg-address">Address</label>
                  <input
                    id="reg-address"
                    type="text"
                    placeholder="123 Main St"
                    value={formAddress}
                    onChange={(e) => setFormAddress(e.target.value)}
                  />
                </div>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={submitting || !formName || !formEmail}>
                  {submitting ? "Registering..." : "Register"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Toast */}
      {toast && (
        <div className={`toast ${toast.type}`}>{toast.message}</div>
      )}
    </>
  );
}
