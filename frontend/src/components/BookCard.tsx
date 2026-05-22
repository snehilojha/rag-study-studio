import type { Book } from "../types";

interface Props {
  book: Book;
  onSelect: (book: Book) => void;
  onDelete: (bookId: number) => void;
  disabled?: boolean;
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function BookCard({ book, onSelect, onDelete, disabled }: Props) {
  const isReady = book.status === "ready";

  return (
    <div className="group flex items-center gap-4 px-4 py-3 border-b border-[#E4E4E4] last:border-b-0 hover:bg-[#F4F4F4] transition-colors">
      <button
        className={`flex-1 text-left text-sm text-[#111] ${
          isReady ? "font-medium hover:underline cursor-pointer" : "font-normal opacity-50 cursor-default"
        }`}
        disabled={!isReady || disabled}
        onClick={() => onSelect(book)}
      >
        {book.title}
      </button>

      <span
        className={`shrink-0 text-xs px-2 py-0.5 rounded bg-[#F0F0F0] ${
          isReady ? "text-[#111] font-medium" : "text-[#888] font-normal"
        }`}
      >
        {book.status}
      </span>

      <span className="shrink-0 text-xs text-[#888]">{formatDate(book.uploaded_at)}</span>

      <button
        className="shrink-0 text-lg leading-none text-[#bbb] hover:text-[#111] opacity-0 group-hover:opacity-100 transition-opacity"
        disabled={disabled}
        onClick={() => onDelete(book.id)}
        aria-label="Delete book"
      >
        ×
      </button>
    </div>
  );
}
