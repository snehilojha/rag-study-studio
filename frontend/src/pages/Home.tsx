// Home page.

import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

import { useBookStore } from "../store/useBookStore";
import { BookCard } from "../components/BookCard";
import { UploadZone } from "../components/UploadZone";
import type { Book } from "../types";

export function Home() {
  const navigate = useNavigate();
  const { books, isLoading, error, fetchBooks, uploadBook, deleteBook } = useBookStore();

  useEffect(() => {
    fetchBooks();
  }, [fetchBooks]);

  function handleSelect(book: Book) {
    navigate(`/books/${book.id}/chapters`);
  }

  return (
    <div>
      <h1>My Books</h1>

      <UploadZone onFile={uploadBook} disabled={isLoading} />

      {error && <p>Error: {error}</p>}

      {isLoading && <p>Loading...</p>}

      {!isLoading && books.length === 0 && (
        <p>No books yet. Upload a PDF to get started.</p>
      )}

      <ul>
        {books.map((book) => (
          <li key={book.id}>
            <BookCard
              book={book}
              onSelect={handleSelect}
              onDelete={deleteBook}
              disabled={isLoading}
            />
          </li>
        ))}
      </ul>
    </div>
  );
}
