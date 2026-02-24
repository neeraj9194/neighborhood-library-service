const API_BASE = process.env.NEXT_PUBLIC_API_BASE;

/* ── Endpoint Paths ────────────────────────────────────────────────── */
const ENDPOINTS = {
  STATS: `${API_BASE}/stats/`,
  BOOKS: `${API_BASE}/books/`,
  BOOK: (id: number) => `${API_BASE}/books/${id}`,
  MEMBERS: `${API_BASE}/members/`,
  MEMBER: (id: number) => `${API_BASE}/members/${id}`,
  BORROW: `${API_BASE}/borrow/`,
  BORROW_RETURN: (id: number) => `${API_BASE}/borrow/${id}/return`,
  BORROW_OVERDUE: `${API_BASE}/borrow/overdue`,
} as const;

/* ── Types ─────────────────────────────────────────────────────────── */
export interface Stats {
  total_books: number;
  total_copies: number;
  available_copies: number;
  borrowed_copies: number;
  total_members: number;
  active_members: number;
  overdue_count: number;
}

export interface Book {
  id: number;
  title: string;
  author: string;
  isbn: string | null;
  genre: string | null;
  publisher: string | null;
  total_copies: number;
  available_copies: number;
  created_at: string;
  updated_at: string;
}

export interface BookListResponse {
  items: Book[];
  total: number;
  page: number;
  size: number;
}

export interface BorrowRecord {
  id: number;
  book_id: number;
  member_id: number;
  borrowed_at: string;
  due_date: string;
  returned_at: string | null;
  status: string;
  book_title: string | null;
  book_author: string | null;
  member_name: string | null;
  member_email: string | null;
}

export interface Member {
  id: number;
  name: string;
  email: string;
  phone: string | null;
  address: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface MemberListResponse {
  items: Member[];
  total: number;
  page: number;
  size: number;
}

export interface BorrowerListResponse {
  items: BorrowRecord[];
  total: number;
  page: number;
  size: number;
}

/* ── Helper ────────────────────────────────────────────────────────── */
async function parseError(res: Response, fallback: string): Promise<string> {
  try {
    const err = await res.json();
    if (Array.isArray(err.detail)) {
      return err.detail
        .map((e: { loc?: string[]; msg?: string }) => {
          const field = e.loc?.filter((s) => s !== "body").join(".") || "";
          return field ? `${field}: ${e.msg}` : (e.msg || fallback);
        })
        .join("; ");
    }
    return typeof err.detail === "string" ? err.detail : fallback;
  } catch {
    return fallback;
  }
}

/* ── Stats ─────────────────────────────────────────────────────────── */
export async function fetchStats(): Promise<Stats> {
  const res = await fetch(ENDPOINTS.STATS);
  if (!res.ok) throw new Error("Failed to load stats");
  return res.json();
}

/* ── Books ─────────────────────────────────────────────────────────── */
export async function fetchBooks(params: {
  page?: number;
  size?: number;
  search?: string;
  genre?: string;
}): Promise<BookListResponse> {
  const sp = new URLSearchParams();
  if (params.page) sp.set("page", String(params.page));
  if (params.size) sp.set("size", String(params.size));
  if (params.search) sp.set("search", params.search);
  if (params.genre) sp.set("genre", params.genre);
  const res = await fetch(`${ENDPOINTS.BOOKS}?${sp.toString()}`);
  if (!res.ok) throw new Error("Failed to load books");
  return res.json();
}

export async function fetchBook(id: number): Promise<Book> {
  const res = await fetch(ENDPOINTS.BOOK(id));
  if (!res.ok) throw new Error("Book not found");
  return res.json();
}

export async function createBook(data: {
  title: string;
  author: string;
  isbn?: string;
  genre?: string;
  publisher?: string;
  total_copies?: number;
}): Promise<Book> {
  const res = await fetch(ENDPOINTS.BOOKS, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await parseError(res, "Failed to create book"));
  return res.json();
}

export async function updateBook(
  id: number,
  data: {
    title?: string;
    author?: string;
    isbn?: string | null;
    genre?: string | null;
    publisher?: string | null;
    total_copies?: number;
  },
): Promise<Book> {
  const res = await fetch(ENDPOINTS.BOOK(id), {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await parseError(res, "Failed to update book"));
  return res.json();
}

export async function deleteBook(id: number): Promise<void> {
  const res = await fetch(ENDPOINTS.BOOK(id), { method: "DELETE" });
  if (!res.ok) throw new Error(await parseError(res, "Failed to delete book"));
}

/* ── Borrow / Return ───────────────────────────────────────────────── */
export async function borrowBook(bookId: number, memberId: number, borrowDays?: number): Promise<BorrowRecord> {
  const body: Record<string, number> = { book_id: bookId, member_id: memberId };
  if (borrowDays) body.borrow_days = borrowDays;
  const res = await fetch(ENDPOINTS.BORROW, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await parseError(res, "Borrow failed"));
  return res.json();
}

export async function fetchBorrowers(params: {
  page?: number;
  size?: number;
  bookId?: number;
}): Promise<BorrowerListResponse> {
  const sp = new URLSearchParams();
  if (params.page) sp.set("page", String(params.page));
  if (params.size) sp.set("size", String(params.size));
  if (params.bookId) sp.set("book_id", String(params.bookId));
  const res = await fetch(`${ENDPOINTS.BORROW}?${sp.toString()}`);
  if (!res.ok) throw new Error("Failed to load borrowers");
  return res.json();
}

export async function fetchOverdue(params: {
  page?: number;
  size?: number;
}): Promise<BorrowerListResponse> {
  const sp = new URLSearchParams();
  if (params.page) sp.set("page", String(params.page));
  if (params.size) sp.set("size", String(params.size));
  const res = await fetch(`${ENDPOINTS.BORROW_OVERDUE}?${sp.toString()}`);
  if (!res.ok) throw new Error("Failed to load overdue records");
  return res.json();
}

export async function returnBook(borrowId: number): Promise<BorrowRecord> {
  const res = await fetch(ENDPOINTS.BORROW_RETURN(borrowId), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error(await parseError(res, "Failed to return book"));
  return res.json();
}

/* ── Members ───────────────────────────────────────────────────────── */
export async function fetchMembers(params: {
  page?: number;
  size?: number;
  search?: string;
  is_active?: boolean;
}): Promise<MemberListResponse> {
  const sp = new URLSearchParams();
  if (params.page) sp.set("page", String(params.page));
  if (params.size) sp.set("size", String(params.size));
  if (params.search) sp.set("search", params.search);
  if (params.is_active !== undefined) sp.set("is_active", String(params.is_active));
  const res = await fetch(`${ENDPOINTS.MEMBERS}?${sp.toString()}`);
  if (!res.ok) throw new Error("Failed to load members");
  return res.json();
}

export async function createMember(data: {
  name: string;
  email: string;
  phone?: string;
  address?: string;
}): Promise<Member> {
  const res = await fetch(ENDPOINTS.MEMBERS, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await parseError(res, "Failed to create member"));
  return res.json();
}

export async function updateMember(
  id: number,
  data: {
    name?: string;
    email?: string;
    phone?: string | null;
    address?: string | null;
    is_active?: boolean;
  },
): Promise<Member> {
  const res = await fetch(ENDPOINTS.MEMBER(id), {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await parseError(res, "Failed to update member"));
  return res.json();
}

export async function deactivateMember(memberId: number): Promise<Member> {
  const res = await fetch(ENDPOINTS.MEMBER(memberId), {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(await parseError(res, "Failed to deactivate member"));
  return res.json();
}
