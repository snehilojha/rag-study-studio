import { useState, useRef, useEffect } from "react";
import { useStudyStore } from "../store/useStudyStore";
import type { QAMessage } from "../types";

interface Props {
  bookId: number;
  topicId: number;
}

function MessageThread({ messages }: { messages: QAMessage[] }) {
  const [openSources, setOpenSources] = useState<Set<number>>(new Set());

  function toggleSources(i: number) {
    setOpenSources((prev) => {
      const next = new Set(prev);
      next.has(i) ? next.delete(i) : next.add(i);
      return next;
    });
  }

  return (
    <div className="space-y-6">
      {messages.map((msg, i) => (
        <div key={i} className="space-y-2">
          {/* Question */}
          <p className="text-xs font-semibold text-[#555]">Q: {msg.question}</p>

          {/* Answer */}
          <p className="text-sm text-[#111] leading-relaxed">{msg.response.answer}</p>

          {/* Sources */}
          {msg.response.citations.length > 0 && (
            <div>
              <button
                onClick={() => toggleSources(i)}
                className="text-xs text-[#888] hover:text-[#111] transition-colors"
              >
                {openSources.has(i) ? "Hide sources" : `Sources (${msg.response.citations.length})`}
              </button>
              {openSources.has(i) && (
                <div className="mt-2 space-y-1 border-l-2 border-[#E4E4E4] pl-3">
                  {msg.response.citations.map((c, ci) => (
                    <p key={ci} className="text-xs text-[#555] leading-relaxed">
                      {c.page_number != null && (
                        <span className="font-medium text-[#333]">p.{c.page_number} — </span>
                      )}
                      {c.text}
                    </p>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

export function QAView({ bookId, topicId }: Props) {
  const { qaMessages, qaLoading, error, askQuestion, clearQA } = useStudyStore();
  const [input, setInput] = useState("");
  const [scopedToTopic, setScopedToTopic] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when a new message is added
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [qaMessages.length]);

  // Reset thread when topic changes
  useEffect(() => {
    clearQA();
  }, [topicId]); // eslint-disable-line react-hooks/exhaustive-deps

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const q = input.trim();
    if (!q || qaLoading) return;
    setInput("");
    await askQuestion(bookId, q, scopedToTopic ? topicId : null);
  }

  return (
    <div className="flex flex-col h-full max-w-2xl">
      {/* Thread */}
      <div className="flex-1 overflow-y-auto pb-4">
        {qaMessages.length === 0 && !qaLoading && (
          <p className="text-sm text-[#888]">Ask anything about this topic.</p>
        )}
        <MessageThread messages={qaMessages} />
        {qaLoading && (
          <p className="text-sm text-[#aaa] mt-4">Thinking…</p>
        )}
        {error && (
          <p className="text-sm text-[#111] mt-4">Error: {error}</p>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="shrink-0 pt-4 border-t border-[#E4E4E4] space-y-2">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question…"
            disabled={qaLoading}
            className="flex-1 text-sm border border-[#E4E4E4] rounded px-3 py-2 bg-white text-[#111] placeholder-[#bbb] focus:outline-none focus:border-[#aaa] transition-colors"
          />
          <button
            type="submit"
            disabled={qaLoading || !input.trim()}
            className="shrink-0 text-sm px-4 py-2 border border-[#E4E4E4] rounded text-[#111] hover:bg-[#F4F4F4] transition-colors disabled:opacity-40"
          >
            Ask
          </button>
        </form>

        <label className="flex items-center gap-2 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={scopedToTopic}
            onChange={(e) => setScopedToTopic(e.target.checked)}
            className="accent-[#555]"
          />
          <span className="text-xs text-[#888]">Scope to this topic</span>
        </label>
      </div>
    </div>
  );
}
