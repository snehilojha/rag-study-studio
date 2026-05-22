import { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";

import { useBookStore } from "../store/useBookStore";
import { useStudyStore } from "../store/useStudyStore";
import { TheoryView } from "../components/TheoryView";
import { PracticalView } from "../components/PracticalView";
import { QAView } from "../components/QuizView";
import { ConnectedTopics } from "../components/ConnectedTopics";

type Tab = "theory" | "practical" | "qa";

function Skeleton() {
  return (
    <div className="space-y-4 max-w-2xl animate-pulse">
      <div className="h-4 bg-[#EFEFEF] rounded w-full" />
      <div className="h-4 bg-[#EFEFEF] rounded w-5/6" />
      <div className="h-4 bg-[#EFEFEF] rounded w-4/6" />
      <div className="h-4 bg-[#EFEFEF] rounded w-full mt-6" />
      <div className="h-4 bg-[#EFEFEF] rounded w-3/4" />
    </div>
  );
}

export function TopicStudy() {
  const { bookId, topicId } = useParams<{ bookId: string; topicId: string }>();
  const navigate = useNavigate();
  const bId = Number(bookId);
  const tId = Number(topicId);

  const [activeTab, setActiveTab] = useState<Tab>("theory");

  const { books, allTopics, fetchBooks, fetchAllTopics } = useBookStore();
  const {
    theory, practical,
    theoryLoading, practicalLoading,
    fetchTheory, fetchPractical,
  } = useStudyStore();

  // Ensure book list is loaded
  useEffect(() => {
    if (books.length === 0) fetchBooks();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Ensure topics are loaded for breadcrumb
  useEffect(() => {
    if (allTopics.length === 0) fetchAllTopics(bId);
  }, [bId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Fetch content for active tab
  useEffect(() => {
    if (activeTab === "theory") fetchTheory(tId);
    if (activeTab === "practical") fetchPractical(tId);
  }, [activeTab, tId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Also pre-fetch theory on mount so it's ready when the page loads
  useEffect(() => {
    fetchTheory(tId);
  }, [tId]); // eslint-disable-line react-hooks/exhaustive-deps

  const book = books.find((b) => b.id === bId);
  const topic = allTopics.find((t) => t.id === tId);

  const theoryContent = theory[tId];
  const practicalContent = practical[tId];

  return (
    <div className="min-h-screen bg-[#FAFAFA]">
      {/* ------------------------------------------------------------------ */}
      {/* Breadcrumb header                                                   */}
      {/* ------------------------------------------------------------------ */}
      <header className="border-b border-[#E4E4E4] bg-white px-6 py-3">
        <nav className="flex items-center gap-1.5 text-xs text-[#888] flex-wrap">
          <Link to="/" className="hover:text-[#111] transition-colors">
            Library
          </Link>
          <span>›</span>
          <Link to={`/books/${bId}`} className="hover:text-[#111] transition-colors">
            {book?.title ?? "Book"}
          </Link>
          {topic && (
            <>
              <span>›</span>
              <Link to={`/books/${bId}`} className="hover:text-[#111] transition-colors">
                Ch.{topic.chapter_order_index}: {topic.chapter_title}
              </Link>
              <span>›</span>
              <span className="text-[#111] font-medium">{topic.title}</span>
            </>
          )}
        </nav>
      </header>

      {/* ------------------------------------------------------------------ */}
      {/* Main layout: content + connected topics panel                       */}
      {/* ------------------------------------------------------------------ */}
      <div className="flex gap-0 h-[calc(100vh-49px)]">
        {/* Content area */}
        <div className="flex-1 overflow-y-auto px-8 py-6">
          {/* Topic title */}
          <h1 className="text-lg font-semibold text-[#111] mb-1">
            {topic?.title ?? "Loading…"}
          </h1>
          {topic?.summary && (
            <p className="text-xs text-[#888] mb-6 leading-relaxed">{topic.summary}</p>
          )}

          {/* Tabs */}
          <div className="flex gap-0 border-b border-[#E4E4E4] mb-6">
            {(["theory", "practical", "qa"] as Tab[]).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 text-sm capitalize border-b-2 transition-colors ${
                  activeTab === tab
                    ? "border-[#111] text-[#111] font-medium"
                    : "border-transparent text-[#888] hover:text-[#555]"
                }`}
              >
                {tab === "qa" ? "Q&A" : tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>

          {/* Tab content */}
          {activeTab === "theory" && (
            theoryLoading && !theoryContent
              ? <Skeleton />
              : theoryContent
                ? <TheoryView content={theoryContent} />
                : <p className="text-sm text-[#888]">No theory content yet.</p>
          )}

          {activeTab === "practical" && (
            practicalLoading && !practicalContent
              ? <Skeleton />
              : practicalContent
                ? <PracticalView content={practicalContent} />
                : <p className="text-sm text-[#888]">No practical content yet.</p>
          )}

          {activeTab === "qa" && (
            <div className="h-[calc(100vh-240px)]">
              <QAView bookId={bId} topicId={tId} />
            </div>
          )}
        </div>

        {/* Connected topics panel */}
        <div className="shrink-0 w-[280px] overflow-y-auto px-6 py-6 border-l border-[#E4E4E4]">
          <ConnectedTopics topicId={tId} bookId={bId} />
        </div>
      </div>
    </div>
  );
}
