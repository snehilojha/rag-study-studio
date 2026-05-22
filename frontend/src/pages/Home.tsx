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
    navigate(`/books/${book.id}`);
  }

  return (
    <div className="min-h-screen bg-[#FAFAFA]">
      <div className="max-w-2xl mx-auto px-6 py-12">
        <h1 className="text-xl font-semibold text-[#111] mb-8">Your Library</h1>

        <UploadZone onFile={uploadBook} disabled={isLoading} />

        {error && (
          <p className="mt-4 text-sm text-[#111]">Error: {error}</p>
        )}

        {!isLoading && books.length === 0 && !error && (
          <p className="mt-8 text-sm text-[#888]">No books yet. Upload a PDF to get started.</p>
        )}

        {books.length > 0 && (
          <div className="mt-8 border border-[#E4E4E4] rounded overflow-hidden">
            {books.map((book) => (
              <BookCard
                key={book.id}
                book={book}
                onSelect={handleSelect}
                onDelete={deleteBook}
                disabled={isLoading}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
