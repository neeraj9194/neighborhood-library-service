"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import DataTable, { type Column } from "@/components/DataTable";
import ConfirmDialog from "@/components/ConfirmDialog";
import Toast from "@/components/Toast";
import {
  fetchBook,
  borrowBook,
  updateBook,
  type Book,
  fetchBorrowers,
  BorrowRecord,
  returnBook,
} from "@/lib/api";

export default function BookDetailPage() {
  const params = useParams();
  const bookId = Number(params.id);
  const [borrower, setBorrower] = useState<BorrowRecord[]>([]);
  const page = 1;
  const size = 20;

  const [book, setBook] = useState<Book | null>(null);
  const [loading, setLoading] = useState(true);

  // Borrow form
  const [memberId, setMemberId] = useState("");
  const [borrowDays, setBorrowDays] = useState("14");
  const [borrowing, setBorrowing] = useState(false);

  // Return confirmation state
  const [confirmReturn, setConfirmReturn] = useState<BorrowRecord | null>(null);
  const [returning, setReturning] = useState(false);

  // Edit modal state
  const [showEditModal, setShowEditModal] = useState(false);
  const [editTitle, setEditTitle] = useState("");
  const [editAuthor, setEditAuthor] = useState("");
  const [editIsbn, setEditIsbn] = useState("");
  const [editGenre, setEditGenre] = useState("");
  const [editPublisher, setEditPublisher] = useState("");
  const [editCopies, setEditCopies] = useState("1");
  const [editSubmitting, setEditSubmitting] = useState(false);
  const [editErrors, setEditErrors] = useState<Record<string, string>>({});

  // Toast state
  const [toast, setToast] = useState<{ type: "success" | "error"; message: string } | null>(null);

  const showToast = (type: "success" | "error", message: string) => {
    setToast({ type, message });
    setTimeout(() => setToast(null), 4000);
  };

  useEffect(() => {
    if (!bookId) return;
    Promise
        .all([fetchBook(bookId), getBorrower(bookId)])
        .then(([bookData]) => { setBook(bookData) })
        .catch((err) => showToast("error", err instanceof Error ? err.message : "Failed to load book"))
        .finally(() => setLoading(false));
  }, [bookId]);

  const handleBorrow = async () => {
    if (!memberId.trim()) return;
    setBorrowing(true);
    try {
      const record = await borrowBook(bookId, Number(memberId), Number(borrowDays) || undefined);
      showToast(
        "success",
        `Borrowed successfully! Due: ${new Date(record.due_date).toLocaleDateString()}`
      );
      const updated = await fetchBook(bookId);
      await getBorrower(bookId);
      setBook(updated);
      setMemberId("");
    } catch (err: unknown) {
      showToast("error", err instanceof Error ? err.message : "Borrow failed");
    } finally {
      setBorrowing(false);
    }
  };

  const getBorrower = async (id: number) => {
    try {
      const record = await fetchBorrowers({ page, size, bookId: id });
      setBorrower(record.items);
    } catch (err: unknown) {
      showToast("error", err instanceof Error ? err.message : "Fetching borrower list failed");
    }
  };

  const handleReturn = async () => {
    if (!confirmReturn) return;
    setReturning(true);
    try {
      await returnBook(confirmReturn.id);
      showToast("success", `Book has been returned by "${confirmReturn.member_name}".`);
      const updated = await fetchBook(bookId);
      await getBorrower(bookId);
      setBook(updated);
      setMemberId("");
    } catch (err: unknown) {
      showToast("error", err instanceof Error ? err.message : "Return failed");
    } finally {
      setReturning(false);
      setConfirmReturn(null);
    }
  };

  /* ── Edit Book ─────────────────────────────────────────────────────── */
  const openEditModal = () => {
    if (!book) return;
    setEditTitle(book.title);
    setEditAuthor(book.author);
    setEditIsbn(book.isbn || "");
    setEditGenre(book.genre || "");
    setEditPublisher(book.publisher || "");
    setEditCopies(String(book.total_copies));
    setEditErrors({});
    setShowEditModal(true);
  };

  const validateEdit = (): boolean => {
    const errors: Record<string, string> = {};
    if (!editTitle.trim()) errors.title = "Title is required";
    if (!editAuthor.trim()) errors.author = "Author is required";
    const copies = Number(editCopies);
    if (!editCopies.trim() || isNaN(copies) || copies < 1) errors.copies = "At least 1 copy required";
    setEditErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleEditBook = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateEdit()) return;
    setEditSubmitting(true);
    try {
      const updated = await updateBook(bookId, {
        title: editTitle.trim(),
        author: editAuthor.trim(),
        isbn: editIsbn.trim() || null,
        genre: editGenre.trim() || null,
        publisher: editPublisher.trim() || null,
        total_copies: Number(editCopies),
      });
      setBook(updated);
      showToast("success", "Book updated successfully!");
      setShowEditModal(false);
    } catch (err: unknown) {
      showToast("error", err instanceof Error ? err.message : "Failed to update book");
    } finally {
      setEditSubmitting(false);
    }
  };

  /* ── Borrower Table Columns ────────────────────────────────────────── */
  const borrowerColumns: Column<BorrowRecord>[] = [
    {
      key: "id",
      header: "ID",
      className: "text-muted",
      render: (m) => `#${m.id}`,
    },
    {
      key: "member_id",
      header: "Member ID",
      className: "text-muted",
      render: (m) => `#${m.member_id}`,
    },
    {
      key: "member_name",
      header: "Member Name",
      className: "font-semibold",
    },
    {
      key: "borrowed_at",
      header: "Borrowed At",
      className: "text-secondary",
      render: (m) => new Date(m.borrowed_at).toLocaleDateString(),
    },
    {
      key: "due_date",
      header: "Due Date",
      className: "text-secondary",
      render: (m) => new Date(m.due_date).toLocaleDateString(),
    },
    {
      key: "returned_at",
      header: "Returned At",
      className: "text-secondary",
      render: (m) => m.returned_at ? new Date(m.returned_at).toLocaleDateString() : "",
    },
    {
      key: "status",
      header: "Status/Action",
      render: (m) => (
        <div className="actions-cell" style={{ justifyContent: "flex-start" }}>
          {m.status === "RETURNED" ? (
            <span className="text-muted">{m.status}</span>
          ) : (
            <>
              <button
                className="btn btn-danger btn-sm"
                onClick={() => setConfirmReturn(m)}
                disabled={returning}
              >
                Return
              </button>
              {m.status === "OVERDUE" && (
                <span className="badge inactive">
                  <span className="badge-dot" /> Overdue
                </span>
              )}
            </>
          )}
        </div>
      ),
    },
  ];

  if (loading) {
    return (
      <>
        <div className="loading-skeleton" style={{ height: 24, width: 100, marginBottom: 24 }} />
        <div className="book-detail">
          <div className="loading-skeleton" style={{ height: 300 }} />
          <div className="loading-skeleton" style={{ height: 300, width: 300 }} />
          <div className="loading-skeleton" style={{ height: 500, width: 800 }} />
        </div>
      </>
    );
  }

  if (!book) {
    return (
      <>
        <Link href="/books" className="back-link">
          ← Back to Books
        </Link>
        <p className="text-muted">Book not found.</p>
      </>
    );
  }

  const hasAvailable = book.available_copies > 0;

  return (
    <>
      <Link href="/books" className="back-link">
        ← Back to Books
      </Link>

      <div className="book-detail">
        {/* Main info */}
        <div className="book-detail-main">
          <div className="book-detail-header">
            <div>
              {book.genre && <span className="book-card-genre">{book.genre}</span>}
              <h2>{book.title}</h2>
              <p className="book-detail-author">by {book.author}</p>
            </div>
            <button className="btn btn-warning btn-sm" onClick={openEditModal}>
              ✏️ Edit
            </button>
          </div>

          <div className="book-detail-info">
            <div className="book-detail-field">
              <label>ISBN</label>
              <span>{book.isbn || "—"}</span>
            </div>
            <div className="book-detail-field">
              <label>Publisher</label>
              <span>{book.publisher || "—"}</span>
            </div>
            <div className="book-detail-field">
              <label>Total Copies</label>
              <span>{book.total_copies}</span>
            </div>
            <div className="book-detail-field">
              <label>Available Copies</label>
              <span className={`copies-available ${hasAvailable ? "has-copies" : "no-copies"}`}>
                {book.available_copies}
              </span>
            </div>
            <div className="book-detail-field">
              <label>Added</label>
              <span>{new Date(book.created_at).toLocaleDateString()}</span>
            </div>
            <div className="book-detail-field">
              <label>Last Updated</label>
              <span>{new Date(book.updated_at).toLocaleDateString()}</span>
            </div>
          </div>
        </div>

        {/* Borrow panel */}
        <div className="borrow-panel">
          <h3>Borrow this Book</h3>

          <div className={`availability ${hasAvailable ? "available" : "unavailable"}`}>
            {hasAvailable ? "✓" : "✗"} {hasAvailable ? `${book.available_copies} copies available` : "No copies available"}
          </div>

          {hasAvailable && (
            <div className="borrow-form">
              <div className="form-group">
                <label htmlFor="member-id">Member ID</label>
                <input
                  id="member-id"
                  type="number"
                  min="1"
                  placeholder="Enter member ID"
                  value={memberId}
                  onChange={(e) => setMemberId(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label htmlFor="borrow-days">Borrow Duration (days)</label>
                <input
                  id="borrow-days"
                  type="number"
                  min="1"
                  max="90"
                  value={borrowDays}
                  onChange={(e) => setBorrowDays(e.target.value)}
                />
              </div>

              <button
                className="btn btn-primary"
                onClick={handleBorrow}
                disabled={borrowing || !memberId.trim()}
              >
                {borrowing ? "Borrowing..." : "Borrow Book"}
              </button>
            </div>
          )}
        </div>

        {/* Borrower Activity */}
        <div className="borrower-list-panel">
          <h3>Recent Activity</h3>
          <DataTable
            columns={borrowerColumns}
            data={borrower}
            rowKey={(m) => m.id}
            emptyMessage="No borrow records yet."
          />
        </div>
      </div>

      {/* Return Confirmation Dialog */}
      {confirmReturn && (
        <ConfirmDialog
          title="Return Book"
          message={`Confirm return of this book from "${confirmReturn.member_name || `Member #${confirmReturn.member_id}`}"?`}
          confirmLabel="Return"
          variant="danger"
          loading={returning}
          onConfirm={handleReturn}
          onCancel={() => setConfirmReturn(null)}
        />
      )}

      {/* Edit Book Modal */}
      {showEditModal && (
        <div className="modal-overlay" onClick={() => setShowEditModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Edit Book</h3>
            <form onSubmit={handleEditBook}>
              <div className="borrow-form">
                <div className="form-group">
                  <label htmlFor="edit-title">Title *</label>
                  <input
                    id="edit-title"
                    type="text"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                  />
                  {editErrors.title && <span className="field-error">{editErrors.title}</span>}
                </div>
                <div className="form-group">
                  <label htmlFor="edit-author">Author *</label>
                  <input
                    id="edit-author"
                    type="text"
                    value={editAuthor}
                    onChange={(e) => setEditAuthor(e.target.value)}
                  />
                  {editErrors.author && <span className="field-error">{editErrors.author}</span>}
                </div>
                <div className="form-group">
                  <label htmlFor="edit-isbn">ISBN</label>
                  <input
                    id="edit-isbn"
                    type="text"
                    value={editIsbn}
                    onChange={(e) => setEditIsbn(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="edit-genre">Genre</label>
                  <input
                    id="edit-genre"
                    type="text"
                    value={editGenre}
                    onChange={(e) => setEditGenre(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="edit-publisher">Publisher</label>
                  <input
                    id="edit-publisher"
                    type="text"
                    value={editPublisher}
                    onChange={(e) => setEditPublisher(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="edit-copies">Total Copies *</label>
                  <input
                    id="edit-copies"
                    type="number"
                    min="1"
                    value={editCopies}
                    onChange={(e) => setEditCopies(e.target.value)}
                  />
                  {editErrors.copies && <span className="field-error">{editErrors.copies}</span>}
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

      {/* Toast */}
      {toast && <Toast type={toast.type} message={toast.message} />}
    </>
  );
}
