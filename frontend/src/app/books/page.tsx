"use client";

import { useEffect, useState, useCallback } from "react";
import BookCard from "@/components/BookCard";
import { fetchBooks, type Book } from "@/lib/api";

export default function BooksPage() {
  const [books, setBooks] = useState<Book[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const size = 12;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetchBooks({ page, size, search: search || undefined });
      setBooks(res.items);
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

  return (
    <>
      <div className="page-header">
        <h2>Books</h2>
        <p>Browse and search the library catalog</p>
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

      {loading ? (
        <div className="books-grid">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="loading-skeleton" style={{ height: 200 }} />
          ))}
        </div>
      ) : books.length === 0 ? (
        <p style={{ color: "var(--text-muted)", textAlign: "center", padding: 40 }}>
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
    </>
  );
}
