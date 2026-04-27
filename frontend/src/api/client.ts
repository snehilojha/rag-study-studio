// API client — all calls to the FastAPI backend go through here.

import type { Book, Chapter } from "../types";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, options);
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail?.detail ?? `HTTP ${res.status}`);
  }
  // 204 No Content — nothing to parse
  if (res.status === 204) return undefined as T;
  return res.json();
}


// Books


/** Fetch all books, newest first. */
export function getBooks(): Promise<Book[]> {
  return request<Book[]>("/books/");
}

/** Fetch a single book by id. */
export function getBook(bookId: number): Promise<Book> {
  return request<Book>(`/books/${bookId}`);
}

/** Upload a PDF. Returns the created Book (status may be "processing"). */
export function uploadBook(file: File): Promise<Book> {
  const form = new FormData();
  form.append("file", file);
  return request<Book>("/books/", { method: "POST", body: form });
}

/** Delete a book and all its data. */
export function deleteBook(bookId: number): Promise<void> {
  return request<void>(`/books/${bookId}`, { method: "DELETE" });
}


// Chapters


/** Fetch all chapters for a book, ordered by position. */
export function getChapters(bookId: number): Promise<Chapter[]> {
  return request<Chapter[]>(`/chapters/${bookId}`);
}

/** Fetch a single chapter. */
export function getChapter(bookId: number, chapterId: number): Promise<Chapter> {
  return request<Chapter>(`/chapters/${bookId}/${chapterId}`);
}