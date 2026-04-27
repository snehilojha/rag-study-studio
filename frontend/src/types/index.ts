// Shared frontend types — mirrors backend models.py shapes returned by FastAPI.

/** Processing state of a book through the ingestion pipeline. */
export type BookStatus = "pending" | "processing" | "ready" | "failed";

/** A book uploaded by the user. Returned by GET /books and POST /books. */
export interface Book {
  id: number;
  title: string;
  author: string;
  uploaded_at: string; // ISO 8601 datetime string (e.g. "2024-01-15T10:30:00Z")
  status: BookStatus;  // only "ready" books are safe to query
}

/** A chapter extracted from a book's PDF. Returned by GET /books/{id}/chapters. */
export interface Chapter {
  id: number;
  book_id: number;     // foreign key — which book this belongs to
  title: string;
  order_index: number; // 1-based position within the book
  start_page: number;
  end_page: number;
  summary: string | null; // null until AI summary is generated
}