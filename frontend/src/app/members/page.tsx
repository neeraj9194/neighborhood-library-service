"use client";

import { useEffect, useState, useCallback } from "react";
import DataTable, { type Column } from "@/components/DataTable";
import ConfirmDialog from "@/components/ConfirmDialog";
import Toast from "@/components/Toast";
import {
  fetchMembers,
  createMember,
  updateMember,
  deactivateMember,
  type Member,
} from "@/lib/api";

export default function MembersPage() {
  const [members, setMembers] = useState<Member[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const size = 20;

  /* ── Register Modal ────────────────────────────────────────────────── */
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [formName, setFormName] = useState("");
  const [formEmail, setFormEmail] = useState("");
  const [formPhone, setFormPhone] = useState("");
  const [formAddress, setFormAddress] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  /* ── Edit Modal ────────────────────────────────────────────────────── */
  const [showEditModal, setShowEditModal] = useState(false);
  const [editMember, setEditMember] = useState<Member | null>(null);
  const [editName, setEditName] = useState("");
  const [editEmail, setEditEmail] = useState("");
  const [editPhone, setEditPhone] = useState("");
  const [editAddress, setEditAddress] = useState("");
  const [editSubmitting, setEditSubmitting] = useState(false);
  const [editErrors, setEditErrors] = useState<Record<string, string>>({});

  /* ── Confirm Deactivation ──────────────────────────────────────────── */
  const [confirmDeactivate, setConfirmDeactivate] = useState<Member | null>(null);
  const [deactivating, setDeactivating] = useState(false);

  /* ── Toast ─────────────────────────────────────────────────────────── */
  const [toast, setToast] = useState<{ type: "success" | "error"; message: string } | null>(null);
  const showToast = (type: "success" | "error", message: string) => {
    setToast({ type, message });
    setTimeout(() => setToast(null), 4000);
  };

  /* ── Data Loading ──────────────────────────────────────────────────── */
  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchMembers({ page, size, search: search || undefined });
      setMembers(res.items);
      setTotal(res.total);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to load members";
      setError(msg);
      showToast("error", msg);
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

  /* ── Register Form ─────────────────────────────────────────────────── */
  const resetRegisterForm = () => {
    setFormName("");
    setFormEmail("");
    setFormPhone("");
    setFormAddress("");
    setFormErrors({});
  };

  const validateRegister = (): boolean => {
    const errors: Record<string, string> = {};
    if (!formName.trim()) errors.name = "Name is required";
    if (!formEmail.trim()) errors.email = "Email is required";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formEmail.trim())) errors.email = "Invalid email address";
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateRegister()) return;
    setSubmitting(true);
    try {
      await createMember({
        name: formName.trim(),
        email: formEmail.trim(),
        phone: formPhone.trim() || undefined,
        address: formAddress.trim() || undefined,
      });
      showToast("success", `Member "${formName.trim()}" registered successfully!`);
      setShowRegisterModal(false);
      resetRegisterForm();
      load();
    } catch (err: unknown) {
      showToast("error", err instanceof Error ? err.message : "Registration failed");
    } finally {
      setSubmitting(false);
    }
  };

  /* ── Edit Form ─────────────────────────────────────────────────────── */
  const openEditModal = (member: Member) => {
    setEditMember(member);
    setEditName(member.name);
    setEditEmail(member.email);
    setEditPhone(member.phone || "");
    setEditAddress(member.address || "");
    setEditErrors({});
    setShowEditModal(true);
  };

  const validateEdit = (): boolean => {
    const errors: Record<string, string> = {};
    if (!editName.trim()) errors.name = "Name is required";
    if (!editEmail.trim()) errors.email = "Email is required";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(editEmail.trim())) errors.email = "Invalid email address";
    setEditErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editMember || !validateEdit()) return;
    setEditSubmitting(true);
    try {
      await updateMember(editMember.id, {
        name: editName.trim(),
        email: editEmail.trim(),
        phone: editPhone.trim() || null,
        address: editAddress.trim() || null,
      });
      showToast("success", `Member "${editName.trim()}" updated successfully!`);
      setShowEditModal(false);
      load();
    } catch (err: unknown) {
      showToast("error", err instanceof Error ? err.message : "Update failed");
    } finally {
      setEditSubmitting(false);
    }
  };

  /* ── Deactivate ────────────────────────────────────────────────────── */
  const handleDeactivate = async () => {
    if (!confirmDeactivate) return;
    setDeactivating(true);
    try {
      await deactivateMember(confirmDeactivate.id);
      showToast("success", `"${confirmDeactivate.name}" has been deactivated.`);
      load();
    } catch (err: unknown) {
      showToast("error", err instanceof Error ? err.message : "Deactivation failed");
    } finally {
      setDeactivating(false);
      setConfirmDeactivate(null);
    }
  };

  /* ── DataTable Columns ────────────────────────────────────────────── */
  const columns: Column<Member>[] = [
    {
      key: "id",
      header: "ID",
      className: "text-muted",
      render: (m) => `#${m.id}`,
    },
    {
      key: "name",
      header: "Member",
      className: "font-semibold",
    },
    {
      key: "email",
      header: "Email",
    },
    {
      key: "phone",
      header: "Phone",
      className: "text-secondary",
      render: (m) => m.phone || "—",
    },
    {
      key: "status",
      header: "Status",
      render: (m) => (
        <span className={`badge ${m.is_active ? "active" : "inactive"}`}>
          <span className="badge-dot" />
          {m.is_active ? "Active" : "Inactive"}
        </span>
      ),
    },
    {
      key: "created_at",
      header: "Joined",
      className: "text-secondary",
      render: (m) => new Date(m.created_at).toLocaleDateString(),
    },
    {
      key: "actions",
      header: "Action",
      render: (m) => (
        <div className="actions-cell">
          {m.is_active && (
            <>
              <button
                className="btn btn-warning btn-sm"
                onClick={() => openEditModal(m)}
              >
                Edit
              </button>
              <button
                className="btn btn-danger btn-sm"
                onClick={() => setConfirmDeactivate(m)}
              >
                Deactivate
              </button>
            </>
          )}
        </div>
      ),
    },
  ];

  return (
    <>
      <div className="page-header page-header-row">
        <div>
          <h2>Members</h2>
          <p>Manage library members and registrations</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowRegisterModal(true)}>
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

      {error && !loading && (
        <div className="inline-alert error">{error}</div>
      )}

      {/* Table */}
      {loading ? (
        <div className="loading-skeleton" style={{ height: 400 }} />
      ) : members.length === 0 && !error ? (
        <p className="empty-state">
          No members found{search ? ` matching "${search}"` : ""}.
        </p>
      ) : (
        <>
          <DataTable
            columns={columns}
            data={members}
            rowKey={(m) => m.id}
            emptyMessage={`No members found${search ? ` matching "${search}"` : ""}.`}
          />

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
      {showRegisterModal && (
        <div className="modal-overlay" onClick={() => setShowRegisterModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Register New Member</h3>
            <form onSubmit={handleRegister}>
              <div className="borrow-form">
                <div className="form-group">
                  <label htmlFor="reg-name">Full Name *</label>
                  <input
                    id="reg-name"
                    type="text"
                    placeholder="John Doe"
                    value={formName}
                    onChange={(e) => setFormName(e.target.value)}
                  />
                  {formErrors.name && <span className="field-error">{formErrors.name}</span>}
                </div>
                <div className="form-group">
                  <label htmlFor="reg-email">Email Address *</label>
                  <input
                    id="reg-email"
                    type="email"
                    placeholder="john@example.com"
                    value={formEmail}
                    onChange={(e) => setFormEmail(e.target.value)}
                  />
                  {formErrors.email && <span className="field-error">{formErrors.email}</span>}
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
                <button type="button" className="btn btn-secondary" onClick={() => { setShowRegisterModal(false); resetRegisterForm(); }}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? "Registering..." : "Register"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && editMember && (
        <div className="modal-overlay" onClick={() => setShowEditModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Edit Member</h3>
            <form onSubmit={handleEdit}>
              <div className="borrow-form">
                <div className="form-group">
                  <label htmlFor="edit-name">Full Name *</label>
                  <input
                    id="edit-name"
                    type="text"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                  />
                  {editErrors.name && <span className="field-error">{editErrors.name}</span>}
                </div>
                <div className="form-group">
                  <label htmlFor="edit-email">Email Address *</label>
                  <input
                    id="edit-email"
                    type="email"
                    value={editEmail}
                    onChange={(e) => setEditEmail(e.target.value)}
                  />
                  {editErrors.email && <span className="field-error">{editErrors.email}</span>}
                </div>
                <div className="form-group">
                  <label htmlFor="edit-phone">Phone</label>
                  <input
                    id="edit-phone"
                    type="tel"
                    value={editPhone}
                    onChange={(e) => setEditPhone(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="edit-address">Address</label>
                  <input
                    id="edit-address"
                    type="text"
                    value={editAddress}
                    onChange={(e) => setEditAddress(e.target.value)}
                  />
                </div>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowEditModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={editSubmitting}>
                  {editSubmitting ? "Saving..." : "Save Changes"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Deactivate Confirmation */}
      {confirmDeactivate && (
        <ConfirmDialog
          title="Deactivate Member"
          message={`Deactivate "${confirmDeactivate.name}"? They will no longer be able to borrow books.`}
          confirmLabel="Deactivate"
          variant="danger"
          loading={deactivating}
          onConfirm={handleDeactivate}
          onCancel={() => setConfirmDeactivate(null)}
        />
      )}

      {toast && <Toast type={toast.type} message={toast.message} />}
    </>
  );
}
