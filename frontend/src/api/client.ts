// API client — all calls to the FastAPI backend go through here.

import type {
  Book,
  Chapter,
  Topic,
  Connection,
  TopicConnection,
  TheoryContent,
  PracticalContent,
  QAResponse,
} from "../types";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, options);
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail?.detail ?? `HTTP ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}


// Books


export function getBooks(): Promise<Book[]> {
  return request<Book[]>("/books/");
}

export function getBook(bookId: number): Promise<Book> {
  return request<Book>(`/books/${bookId}`);
}

export function uploadBook(file: File): Promise<Book> {
  const form = new FormData();
  form.append("file", file);
  return request<Book>("/books/", { method: "POST", body: form });
}

export function deleteBook(bookId: number): Promise<void> {
  return request<void>(`/books/${bookId}`, { method: "DELETE" });
}


// Chapters


export function getChapters(bookId: number): Promise<Chapter[]> {
  return request<Chapter[]>(`/chapters/${bookId}`);
}

export function getChapter(bookId: number, chapterId: number): Promise<Chapter> {
  return request<Chapter>(`/chapters/${bookId}/${chapterId}`);
}


// Topics


/** Fetch all topics for a book, each enriched with chapter metadata. */
export function getAllTopicsForBook(bookId: number): Promise<Topic[]> {
  return request<Topic[]>(`/topics/book/${bookId}`);
}


// Connections


/** Fetch all persisted concept edges for a book (fast DB read, no LLM). */
export function getBookConnections(bookId: number): Promise<Connection[]> {
  return request<Connection[]>(`/connections/book/${bookId}`);
}

/** Generate (or retrieve cached) connections for a specific topic. Persists new edges to DB. */
export function getTopicConnections(topicId: number): Promise<TopicConnection[]> {
  return request<TopicConnection[]>(`/study/connections/${topicId}`);
}


// Study content


/** Fetch theory content for a topic (explanation, key points, definitions). */
export function getTheory(topicId: number): Promise<TheoryContent> {
  return request<TheoryContent>(`/study/theory/${topicId}`);
}

/** Fetch practical content for a topic (overview, examples, tips). */
export function getPractical(topicId: number): Promise<PracticalContent> {
  return request<PracticalContent>(`/study/practical/${topicId}`);
}


// Q&A


/** Ask a question scoped to a topic (or the whole book if topicId is null). */
export function askQuestion(
  bookId: number,
  question: string,
  topicId: number | null,
): Promise<QAResponse> {
  return request<QAResponse>("/qa/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ book_id: bookId, question, topic_id: topicId }),
  });
}
