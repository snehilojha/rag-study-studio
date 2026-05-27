import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useBookStore } from '../store/useBookStore';
import { BookCard } from '../components/BookCard';
import { UploadZone } from '../components/UploadZone';
import { Logo } from '../components/ui';
import type { Book } from '../types';

export function Home() {
  const navigate = useNavigate();
  const { books, fetchBooks, uploadBook, deleteBook } = useBookStore();
  const [uploading, setUploading] = useState(false);

  useEffect(() => { fetchBooks(); }, [fetchBooks]);

  async function handleFile(file: File) {
    setUploading(true);
    await uploadBook(file);
    setUploading(false);
  }

  function handleSelect(book: Book) {
    navigate(`/books/${book.id}`);
  }

  function handleDelete(book: Book) {
    if (window.confirm(`Delete "${book.title}"? This cannot be undone.`)) {
      deleteBook(book.id);
    }
  }

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', animation: 'fadeIn 0.3s ease-out' }}>
      <header style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '0 20px', height: 50, borderBottom: '1px solid var(--border)', background: 'var(--surface)', flexShrink: 0 }}>
        <Logo size={22} />
        <span style={{ fontSize: 13, fontWeight: 600 }}>RAG Study Studio</span>
      </header>

      <div style={{ flex: 1, overflow: 'auto', maxWidth: 700, width: '100%', margin: '0 auto', padding: '30px 24px 80px' }}>
        <h1 style={{ fontSize: 20, fontWeight: 600, letterSpacing: '-0.01em', marginBottom: 24 }}>Your Library</h1>

        <UploadZone onFile={handleFile} uploading={uploading} />

        {books.length > 0 && (
          <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--r)', overflow: 'hidden' }}>
            {books.map((book, i) => (
              <BookCard key={book.id} book={book} onSelect={handleSelect} onDelete={handleDelete} idx={i} />
            ))}
          </div>
        )}

        {books.length === 0 && !uploading && (
          <p style={{ fontSize: 13, color: 'var(--text-3)', marginTop: 16 }}>No books yet. Upload a PDF to get started.</p>
        )}
      </div>
    </div>
  );
}
