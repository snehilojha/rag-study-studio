// Shared frontend types — mirrors backend models.py shapes returned by FastAPI.

/** Processing state of a book through the ingestion pipeline. */
export type BookStatus = "pending" | "processing" | "ready" | "failed";

/** A book uploaded by the user. Returned by GET /books and POST /books. */
export interface Book {
  id: number;
  title: string;
  author: string;
  uploaded_at: string;
  status: BookStatus;
}

/** A chapter extracted from a book's PDF. Returned by GET /chapters/{book_id}. */
export interface Chapter {
  id: number;
  book_id: number;
  title: string;
  order_index: number;
  start_page: number;
  end_page: number;
  summary: string | null;
}

/** A topic extracted from a chapter, enriched with chapter metadata.
 *  Returned by GET /topics/book/{book_id}. Used to build the concept graph. */
export interface Topic {
  id: number;
  title: string;
  order_index: number;
  start_page: number;
  end_page: number;
  summary: string | null;
  chapter_id: number;
  chapter_title: string;
  chapter_order_index: number;
}

/** Edge type values matching backend EdgeType enum. */
export type EdgeType = "prerequisite" | "extension" | "application" | "contrast";

/** A concept edge between two topics. Returned by GET /connections/book/{book_id}. */
export interface Connection {
  id: number;
  source_topic_id: number;
  source_topic_title: string;
  source_chapter_id: number;
  source_chapter_title: string;
  target_topic_id: number;
  target_topic_title: string;
  target_chapter_id: number;
  target_chapter_title: string;
  edge_type: EdgeType;
}

/** A connection entry as returned by GET /study/connections/{topic_id}.
 *  Includes the LLM-generated reason and relationship label. */
export interface TopicConnection {
  source_topic: string;
  source_topic_id: number;
  target_topic: string;
  target_topic_id: number;
  relationship: EdgeType;
  valid: boolean;
  reason: string;
}

// ---------------------------------------------------------------------------
// Study content types — returned by GET /study/theory/:id, /study/practical/:id
// ---------------------------------------------------------------------------

export interface Definition {
  term: string;
  definition: string;
}

export interface TheoryContent {
  explanation: string;
  key_points: string[];
  definitions: Definition[];
}

export interface PracticalExample {
  title: string;
  description: string;
  steps: string[];
}

export interface PracticalContent {
  overview: string;
  examples: PracticalExample[];
  tips: string[];
}

// ---------------------------------------------------------------------------
// Q&A types — returned by POST /qa/ask
// ---------------------------------------------------------------------------

export interface Citation {
  text: string;
  page_number: number | null;
  chapter_id: number | null;
  book_id: number | null;
}

export interface QAResponse {
  answer: string;
  citations: Citation[];
}

export interface QAMessage {
  question: string;
  response: QAResponse;
}
