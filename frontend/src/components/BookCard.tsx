import { useState } from 'react';
import { BookCover, Badge } from './ui';
import type { Book } from '../types';

interface Props {
  book: Book;
  onSelect: (book: Book) => void;
  onDelete: (book: Book) => void;
  idx: number;
}

export function BookCard({ book, onSelect, onDelete, idx }: Props) {
  const isReady = book.status === 'ready';
  const [hov, setHov] = useState(false);
  const [delHov, setDelHov] = useState(false);

  return (
    <div
      style={{ display: 'flex', alignItems: 'center', borderBottom: '1px solid var(--border-s)', background: hov && !delHov && isReady ? 'var(--bg)' : 'none', transition: 'background 0.12s' }}
      onMouseEnter={() => setHov(true)}
      onMouseLeave={() => setHov(false)}
    >
      {/* Main clickable area */}
      <button
        onClick={() => isReady && onSelect(book)}
        style={{
          flex: 1, display: 'flex', alignItems: 'center', gap: 16,
          padding: '16px 18px', background: 'none', border: 'none',
          cursor: isReady ? 'pointer' : 'default',
          textAlign: 'left', fontFamily: 'inherit',
        }}
      >
        <BookCover idx={idx} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 9, marginBottom: 5, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 14, fontWeight: 600, letterSpacing: '-0.01em' }}>{book.title}</span>
            <Badge status={book.status} />
          </div>
          <p style={{ fontSize: 12, color: 'var(--text-2)' }}>{book.author}</p>
        </div>
        {isReady && (
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="var(--text-3)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
            <path d="M5 11l4-4-4-4" />
          </svg>
        )}
      </button>

      {/* Delete button */}
      <button
        onClick={() => onDelete(book)}
        title="Delete book"
        onMouseEnter={() => setDelHov(true)}
        onMouseLeave={() => setDelHov(false)}
        style={{
          flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
          width: 34, height: 34, marginRight: 10, background: delHov ? 'var(--rose-bg)' : 'none',
          border: '1px solid', borderColor: delHov ? 'var(--rose)' : 'transparent',
          borderRadius: 6, cursor: 'pointer', transition: 'all 0.12s', color: delHov ? 'var(--rose)' : 'var(--text-3)',
        }}
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M2 3.5h10M5.5 3.5V2.5h3v1M4.5 3.5l.5 8h4l.5-8" />
        </svg>
      </button>
    </div>
  );
}
