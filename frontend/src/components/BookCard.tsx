// Book card component.

import type { Book } from "../types";

interface Props {
  book: Book;
  onSelect: (book: Book) => void;
  onDelete: (bookId: number) => void;
  disabled?: boolean;
}

export function BookCard({ book, onSelect, onDelete, disabled }: Props) {
  return (
    <div>
      <button
        disabled={disabled || book.status !== "ready"}
        onClick={() => onSelect(book)}
      >
        <span>{book.title}</span>
        <span>[{book.status}]</span>
      </button>
      <button
        disabled={disabled}
        onClick={() => onDelete(book.id)}
      >
        Delete
      </button>
    </div>
  );
}
