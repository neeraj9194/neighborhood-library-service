const API_BASE = "http://localhost:8000/api/v1";

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

export async function fetchStats(): Promise<Stats> {
  const res = await fetch(`${API_BASE}/stats/`);
  if (!res.ok) throw new Error("Failed to load stats");
  return res.json();
}

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
  const res = await fetch(`${API_BASE}/books/?${sp.toString()}`);
  if (!res.ok) throw new Error("Failed to load books");
  return res.json();
}

export async function fetchBook(id: number): Promise<Book> {
  const res = await fetch(`${API_BASE}/books/${id}`);
  if (!res.ok) throw new Error("Book not found");
  return res.json();
}

export async function borrowBook(bookId: number, memberId: number, borrowDays?: number): Promise<BorrowRecord> {
  const body: Record<string, number> = { book_id: bookId, member_id: memberId };
  if (borrowDays) body.borrow_days = borrowDays;
  const res = await fetch(`${API_BASE}/borrow/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Borrow failed");
  }
  return res.json();
}

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
  const res = await fetch(`${API_BASE}/members/?${sp.toString()}`);
  if (!res.ok) throw new Error("Failed to load members");
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
  const res = await fetch(`${API_BASE}/borrow/?${sp.toString()}`);
  if (!res.ok) throw new Error("Failed to load borrowers");
  return res.json();
}

export async function createMember(data: {
  name: string;
  email: string;
  phone?: string;
  address?: string;
}): Promise<Member> {
  const res = await fetch(`${API_BASE}/members/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to create member");
  }
  return res.json();
}

export async function deactivateMember(memberId: number): Promise<Member> {
  const res = await fetch(`${API_BASE}/members/${memberId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to deactivate member");
  }
  return res.json();
}

export async function returnBook(borrowId: number): Promise<Member> {
  const res = await fetch(`${API_BASE}/borrow/${borrowId}/return`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to return book");
  }
  return res.json();
}
