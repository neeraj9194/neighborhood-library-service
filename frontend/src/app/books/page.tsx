"use client";

import { useEffect, useState, useCallback } from "react";
import BookCard from "@/components/BookCard";
import Toast from "@/components/Toast";
import { fetchBooks, createBook, type Book } from "@/lib/api";

export default function BooksPage() {
  const [books, setBooks] = useState<Book[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const size = 12;

  /* ── Toast ─────────────────────────────────────────────────────────── */
  const [toast, setToast] = useState<{ type: "success" | "error"; message: string } | null>(null);
  const showToast = (type: "success" | "error", message: string) => {
    setToast({ type, message });
    setTimeout(() => setToast(null), 4000);
  };

  /* ── Add Book Modal ────────────────────────────────────────────────── */
  const [showModal, setShowModal] = useState(false);
  const [formTitle, setFormTitle] = useState("");
  const [formAuthor, setFormAuthor] = useState("");
  const [formIsbn, setFormIsbn] = useState("");
  const [formGenre, setFormGenre] = useState("");
  const [formPublisher, setFormPublisher] = useState("");
  const [formCopies, setFormCopies] = useState("1");
  const [submitting, setSubmitting] = useState(false);
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  const resetForm = () => {
    setFormTitle("");
    setFormAuthor("");
    setFormIsbn("");
    setFormGenre("");
    setFormPublisher("");
    setFormCopies("1");
    setFormErrors({});
  };

  const validateBookForm = (): boolean => {
    const errors: Record<string, string> = {};
    if (!formTitle.trim()) errors.title = "Title is required";
    if (!formAuthor.trim()) errors.author = "Author is required";
    const copies = Number(formCopies);
    if (!formCopies.trim() || isNaN(copies) || copies < 1) errors.copies = "At least 1 copy required";
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleAddBook = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateBookForm()) return;
    setSubmitting(true);
    try {
      await createBook({
        title: formTitle.trim(),
        author: formAuthor.trim(),
        isbn: formIsbn.trim() || undefined,
        genre: formGenre.trim() || undefined,
        publisher: formPublisher.trim() || undefined,
        total_copies: Number(formCopies),
      });
      showToast("success", `"${formTitle.trim()}" added successfully!`);
      setShowModal(false);
      resetForm();
      load();
    } catch (err: unknown) {
      showToast("error", err instanceof Error ? err.message : "Failed to add book");
    } finally {
      setSubmitting(false);
    }
  };

  /* ── Data Loading ──────────────────────────────────────────────────── */
  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchBooks({ page, size, search: search || undefined });
      setBooks(res.items);
      setTotal(res.total);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to load books";
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

  return (
    <>
      <div className="page-header page-header-row">
        <div>
          <h2>Books</h2>
          <p>Browse and search the library catalog</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>
          + Add Book
        </button>
      </div>

      <div className="search-bar">
        <div className="search-input">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8" />
            <path d="M21 21l-4.35-4.35" />
          </svg>
          <input
            type="text"
            placeholder="Search by title or author..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
        </div>
      </div>

      {error && !loading && (
        <div className="inline-alert error">{error}</div>
      )}

      {loading ? (
        <div className="books-grid">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="loading-skeleton" style={{ height: 200 }} />
          ))}
        </div>
      ) : books.length === 0 && !error ? (
        <p className="empty-state">
          No books found{search ? ` matching "${search}"` : ""}.
        </p>
      ) : (
        <>
          <div className="books-grid">
            {books.map((book) => (
              <BookCard key={book.id} book={book} />
            ))}
          </div>

          {totalPages > 1 && (
            <div className="pagination">
              <button className="btn btn-secondary" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                Previous
              </button>
              <span className="pagination-info">
                Page {page} of {totalPages} ({total} books)
              </span>
              <button className="btn btn-secondary" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
                Next
              </button>
            </div>
          )}
        </>
      )}

      {/* Add Book Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Add New Book</h3>
            <form onSubmit={handleAddBook}>
              <div className="borrow-form">
                <div className="form-group">
                  <label htmlFor="book-title">Title *</label>
                  <input
                    id="book-title"
                    type="text"
                    placeholder="The Great Gatsby"
                    value={formTitle}
                    onChange={(e) => setFormTitle(e.target.value)}
                  />
                  {formErrors.title && <span className="field-error">{formErrors.title}</span>}
                </div>
                <div className="form-group">
                  <label htmlFor="book-author">Author *</label>
                  <input
                    id="book-author"
                    type="text"
                    placeholder="F. Scott Fitzgerald"
                    value={formAuthor}
                    onChange={(e) => setFormAuthor(e.target.value)}
                  />
                  {formErrors.author && <span className="field-error">{formErrors.author}</span>}
                </div>
                <div className="form-group">
                  <label htmlFor="book-isbn">ISBN</label>
                  <input
                    id="book-isbn"
                    type="text"
                    placeholder="9780743273565"
                    value={formIsbn}
                    onChange={(e) => setFormIsbn(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="book-genre">Genre</label>
                  <input
                    id="book-genre"
                    type="text"
                    placeholder="Fiction"
                    value={formGenre}
                    onChange={(e) => setFormGenre(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="book-publisher">Publisher</label>
                  <input
                    id="book-publisher"
                    type="text"
                    placeholder="Scribner"
                    value={formPublisher}
                    onChange={(e) => setFormPublisher(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="book-copies">Total Copies *</label>
                  <input
                    id="book-copies"
                    type="number"
                    min="1"
                    value={formCopies}
                    onChange={(e) => setFormCopies(e.target.value)}
                  />
                  {formErrors.copies && <span className="field-error">{formErrors.copies}</span>}
                </div>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => { setShowModal(false); resetForm(); }}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? "Adding..." : "Add Book"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {toast && <Toast type={toast.type} message={toast.message} />}
    </>
  );
}
