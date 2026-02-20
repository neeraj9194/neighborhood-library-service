import Link from "next/link";
import type { Book } from "@/lib/api";

interface BookCardProps {
  book: Book;
}

export default function BookCard({ book }: BookCardProps) {
  const hasAvailable = book.available_copies > 0;

  return (
    <Link href={`/books/${book.id}`} className="book-card">
      {book.genre && <span className="book-card-genre">{book.genre}</span>}
      <h3>{book.title}</h3>
      <p className="book-card-author">by {book.author}</p>
      <div className="book-card-meta">
        <span className={`book-card-copies ${hasAvailable ? "" : "none"}`}>
          <strong>{book.available_copies}</strong> / {book.total_copies} available
        </span>
      </div>
    </Link>
  );
}
