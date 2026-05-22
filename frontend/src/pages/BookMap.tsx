import { useEffect, useMemo, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";

import { useBookStore } from "../store/useBookStore";
import { ConceptGraph } from "../components/ConceptGraph";

export function BookMap() {
  const { bookId } = useParams<{ bookId: string }>();
  const navigate = useNavigate();
  const id = Number(bookId);

  const {
    books,
    chapters,
    allTopics,
    connections,
    isLoading,
    fetchBooks,
    selectBook,
    fetchAllTopics,
    fetchBookConnections,
  } = useBookStore();

  const book = books.find((b) => b.id === id) ?? null;

  // Track open chapters in the accordion
  const [openChapters, setOpenChapters] = useState<Set<number>>(new Set());

  // Load book list if not yet fetched
  useEffect(() => {
    if (books.length === 0) fetchBooks();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // When the book is resolved, load chapters + topics + connections
  useEffect(() => {
    if (!book) return;
    selectBook(book);
    fetchAllTopics(id);
    fetchBookConnections(id);
  }, [id]); // eslint-disable-line react-hooks/exhaustive-deps

  // Group topics by chapter for the sidebar list
  const topicsByChapter = useMemo(() => {
    const map = new Map<number, typeof allTopics>();
    for (const t of allTopics) {
      if (!map.has(t.chapter_id)) map.set(t.chapter_id, []);
      map.get(t.chapter_id)!.push(t);
    }
    return map;
  }, [allTopics]);

  function toggleChapter(chapterId: number) {
    setOpenChapters((prev) => {
      const next = new Set(prev);
      next.has(chapterId) ? next.delete(chapterId) : next.add(chapterId);
      return next;
    });
  }

  // Book not found after load completes
  if (!book && !isLoading && books.length > 0) {
    return (
      <div className="min-h-screen bg-[#FAFAFA] flex items-center justify-center">
        <p className="text-sm text-[#888]">
          Book not found.{" "}
          <Link to="/" className="underline">
            Go home
          </Link>
        </p>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-[#FAFAFA] overflow-hidden">
      {/* ------------------------------------------------------------------ */}
      {/* Left sidebar                                                         */}
      {/* ------------------------------------------------------------------ */}
      <aside className="w-[280px] shrink-0 bg-[#F4F4F4] border-r border-[#E4E4E4] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="px-4 py-4 border-b border-[#E4E4E4] shrink-0">
          <Link
            to="/"
            className="text-xs text-[#888] hover:text-[#111] transition-colors"
          >
            ← Library
          </Link>
          <h2 className="mt-2 text-sm font-semibold text-[#111] leading-snug">
            {book?.title ?? "Loading…"}
          </h2>
        </div>

        {/* Chapter accordion */}
        <nav className="flex-1 overflow-y-auto py-2">
          {chapters.map((chapter) => {
            const topics = topicsByChapter.get(chapter.id) ?? [];
            const isOpen = openChapters.has(chapter.id);
            return (
              <div key={chapter.id}>
                <button
                  onClick={() => toggleChapter(chapter.id)}
                  className="w-full flex items-center justify-between px-4 py-2 text-xs font-semibold text-[#555] hover:text-[#111] hover:bg-[#EBEBEB] transition-colors text-left"
                >
                  <span className="truncate">
                    {chapter.order_index}. {chapter.title}
                  </span>
                  <span className="ml-2 shrink-0 font-normal">{isOpen ? "−" : "+"}</span>
                </button>

                {isOpen && (
                  <div className="pb-1">
                    {topics
                      .slice()
                      .sort((a, b) => a.order_index - b.order_index)
                      .map((topic) => (
                        <button
                          key={topic.id}
                          onClick={() => navigate(`/books/${id}/topics/${topic.id}`)}
                          className="w-full flex items-center justify-between px-6 py-1.5 text-xs text-[#444] hover:text-[#111] hover:bg-[#EBEBEB] transition-colors text-left"
                        >
                          <span className="truncate">{topic.title}</span>
                          <span className="ml-2 shrink-0 text-[#bbb]">p.{topic.start_page}</span>
                        </button>
                      ))}
                  </div>
                )}
              </div>
            );
          })}

          {!isLoading && chapters.length === 0 && (
            <p className="px-4 py-3 text-xs text-[#aaa]">No chapters found.</p>
          )}
        </nav>
      </aside>

      {/* ------------------------------------------------------------------ */}
      {/* Right — concept graph                                               */}
      {/* ------------------------------------------------------------------ */}
      <main className="flex-1 overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center h-full text-sm text-[#888]">
            Loading…
          </div>
        ) : (
          <ConceptGraph topics={allTopics} connections={connections} bookId={id} />
        )}
      </main>
    </div>
  );
}
