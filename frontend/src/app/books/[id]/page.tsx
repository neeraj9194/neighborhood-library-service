"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  fetchBook,
  borrowBook,
  type Book,
  type Member,
  fetchBorrowers,
  BorrowRecord,
  deactivateMember,
  returnBook
} from "@/lib/api";

export default function BookDetailPage() {
  const params = useParams();
  const bookId = Number(params.id);
  const [borrower, setBorrower] = useState<BorrowRecord[]>([]);
  const [page, setPage] = useState(1);
  const size = 20;

  const [book, setBook] = useState<Book | null>(null);
  const [loading, setLoading] = useState(true);

  // Borrow form
  const [memberId, setMemberId] = useState("");
  const [borrowDays, setBorrowDays] = useState("14");
  const [borrowing, setBorrowing] = useState(false);
  const [result, setResult] = useState<{ type: "success" | "error"; message: string } | null>(null);

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
        .catch(console.error)
        .finally(() => setLoading(false));
  }, [bookId]);

  const handleBorrow = async () => {
    if (!memberId) return;
    setBorrowing(true);
    setResult(null);
    try {
      const record = await borrowBook(bookId, Number(memberId), Number(borrowDays) || undefined);
      setResult({
        type: "success",
        message: `Borrowed successfully! Due: ${new Date(record.due_date).toLocaleDateString()}`,
      });
      // Refresh book to get updated availability
      const updated = await fetchBook(bookId);
      await getBorrower(bookId);
      setBook(updated);
      setMemberId("");
    } catch (err: unknown) {
      setResult({ type: "error", message: err instanceof Error ? err.message : "Borrow failed" });
    } finally {
      setBorrowing(false);
    }
  };

  const getBorrower = async (bookId: number) => {
    try {
      const record = await fetchBorrowers({ page, size, bookId});
      setBorrower(record.items);
    } catch (err: unknown) {
      setResult({ type: "error", message: err instanceof Error ? err.message : "Fetching Borrower list failed" });
    } finally {

    }
  };

  const handleReturn = async (borrow: BorrowRecord) => {
    try {
      await returnBook(borrow.id);
      showToast("success", `Book has been returned by "${borrow.member_name}".`);
      const updated = await fetchBook(bookId);
      await getBorrower(bookId);
      setBook(updated);
      setMemberId("");
    } catch (err: unknown) {
      showToast("error", err instanceof Error ? err.message : "Deactivation failed");
    }
  };

  if (loading) {
    return (
      <>
        <div className="loading-skeleton" style={{ height: 24, width: 100, marginBottom: 24 }} />
        <div className="book-detail">
          <div className="loading-skeleton" style={{ height: 300}} />
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
        <p style={{ color: "var(--text-muted)" }}>Book not found.</p>
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
          {book.genre && <span className="book-card-genre">{book.genre}</span>}
          <h2>{book.title}</h2>
          <p className="book-detail-author">by {book.author}</p>

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
              <span style={{ color: hasAvailable ? "var(--success)" : "var(--danger)", fontWeight: 700 }}>
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
                disabled={borrowing || !memberId}
              >
                {borrowing ? "Borrowing..." : "Borrow Book"}
              </button>
            </div>
          )}

          {result && (
            <div className={`borrow-result ${result.type}`}>
              {result.message}
            </div>
          )}
        </div>
        <div className="borrower-list-panel">
          <h3>Recent Activity</h3>
          <div className="data-table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Member ID</th>
                  <th>Member Name</th>
                  {/*<th>Member Email</th>*/}
                  <th>Borrowed At</th>
                  <th>Due Date</th>
                  <th>Returned At</th>
                  <th>Status/Action</th>
                </tr>
              </thead>
              <tbody>
                {borrower.map((m) => (
                  <tr key={m.id}>
                    <td style={{ color: "var(--text-muted)" }}>#{m.id}</td>
                    <td style={{ color: "var(--text-muted)" }}>#{m.member_id}</td>
                    <td style={{ fontWeight: 600 }}>{m.member_name}</td>
                    {/*<td>{m.member_email}</td>*/}
                    <td style={{ color: "var(--text-secondary)" }}>
                      {new Date(m.borrowed_at).toLocaleDateString()}
                    </td>
                    <td style={{ color: "var(--text-secondary)" }}>
                      {new Date(m.due_date).toLocaleDateString()}
                    </td>
                    <td style={{ color: "var(--text-secondary)" }}>
                      {m.returned_at?new Date(m.returned_at).toLocaleDateString():""}
                    </td>
                    <td>
                      {m.status == "BORROWED" && (
                        <button
                          className="btn btn-danger btn-sm"
                          onClick={() => handleReturn(m)}
                        >
                          Return
                        </button>
                      )}
                      {m.status == "RETURNED" && <span style={{ color: "var(--text-muted)" }}>{m.status}</span> }
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Toast */}
      {toast && (
        <div className={`toast ${toast.type}`}>{toast.message}</div>
      )}
    </>
  );
}
