import { BookCover, Badge } from './ui';
import type { Book } from '../types';

interface Props {
  book: Book;
  onSelect: (book: Book) => void;
  idx: number;
}

export function BookCard({ book, onSelect, idx }: Props) {
  const isReady = book.status === 'ready';
  return (
    <button
      onClick={() => isReady && onSelect(book)}
      style={{
        width: '100%', display: 'flex', alignItems: 'center', gap: 16,
        padding: '16px 18px', background: 'none', border: 'none',
        borderBottom: '1px solid var(--border-s)', cursor: isReady ? 'pointer' : 'default',
        textAlign: 'left', fontFamily: 'inherit', transition: 'background 0.12s',
      }}
      onMouseEnter={e => { if (isReady) e.currentTarget.style.background = 'var(--bg)'; }}
      onMouseLeave={e => { e.currentTarget.style.background = 'none'; }}
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
  );
}
