// Chapters page.

import { useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";

import { useBookStore } from "../store/useBookStore";
import { ChapterList } from "../components/ChapterList";
import * as api from "../api/client";
import type { Chapter } from "../types";

export function Chapters() {
  const { bookId } = useParams<{ bookId: string }>();
  const navigate = useNavigate();
  const { books, chapters, isLoading, error, selectBook, selectChapter } = useBookStore();

  const book = books.find((b) => b.id === Number(bookId));

  useEffect(() => {
    if (!bookId) return;
    const id = Number(bookId);

    // If book is already in store, use it — otherwise fetch from API
    const existing = books.find((b) => b.id === id);
    if (existing) {
      selectBook(existing);
    } else {
      api.getBook(id)
        .then((b) => selectBook(b))
        .catch(() => navigate("/"));
    }
  }, [bookId, selectBook, navigate]);

  function handleSelect(chapter: Chapter) {
    selectChapter(chapter);
    // placeholder — navigate to study page when built
  }

  return (
    <div>
      <button onClick={() => navigate("/")}>← Back</button>
      <h1>{book?.title ?? "Chapters"}</h1>

      {error && <p>Error: {error}</p>}
      {isLoading && <p>Loading chapters...</p>}

      {!isLoading && (
        <ChapterList chapters={chapters} onSelect={handleSelect} />
      )}
    </div>
  );
}
