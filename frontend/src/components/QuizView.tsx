import { useState, useRef, useEffect } from 'react';
import { useStudyStore } from '../store/useStudyStore';
import { Spinner } from './ui';
import type { QAMessage } from '../types';

interface Props {
  bookId: number;
  topicId: number;
  topicTitle: string;
}

function Thread({ messages }: { messages: QAMessage[] }) {
  const [openSrc, setOpenSrc] = useState<Set<number>>(new Set());
  function togSrc(i: number) { setOpenSrc(p => { const n = new Set(p); n.has(i) ? n.delete(i) : n.add(i); return n; }); }

  return (
    <>
      {messages.map((m, i) => (
        <div key={i} style={{ marginBottom: 26, animation: 'fadeIn 0.25s ease-out' }}>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 10 }}>
            <div style={{ background: 'var(--text)', color: 'white', padding: '9px 14px', borderRadius: '12px 12px 3px 12px', maxWidth: '80%', fontSize: 13.5, lineHeight: 1.55 }}>
              {m.question}
            </div>
          </div>
          <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '3px 12px 12px 12px', padding: '12px 15px', maxWidth: '92%' }}>
            <p style={{ fontSize: 13.5, lineHeight: 1.74, color: 'var(--text)', marginBottom: m.response.citations?.length ? 10 : 0 }}>{m.response.answer}</p>
            {m.response.citations?.length > 0 && (
              <div>
                <button onClick={() => togSrc(i)}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 11.5, color: 'var(--text-3)', display: 'flex', alignItems: 'center', gap: 4, padding: 0, fontFamily: 'inherit', transition: 'color 0.1s' }}
                  onMouseEnter={e => e.currentTarget.style.color = 'var(--text-2)'}
                  onMouseLeave={e => e.currentTarget.style.color = 'var(--text-3)'}>
                  <svg width="11" height="11" viewBox="0 0 11 11" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"><rect x="0.75" y="0.75" width="9.5" height="9.5" rx="1.5" /><path d="M3 3.5h5M3 5.5h5M3 7.5h3" /></svg>
                  {openSrc.has(i) ? 'Hide sources' : `${m.response.citations.length} source${m.response.citations.length > 1 ? 's' : ''}`}
                </button>
                {openSrc.has(i) && (
                  <div style={{ marginTop: 8, paddingTop: 8, borderTop: '1px solid var(--border-s)', display: 'flex', flexDirection: 'column', gap: 6, animation: 'fadeIn 0.15s ease-out' }}>
                    {m.response.citations.map((c, ci) => (
                      <div key={ci} style={{ display: 'flex', gap: 9, padding: '6px 10px', background: 'var(--bg)', borderRadius: 'var(--r-sm)' }}>
                        {c.page_number != null && (
                          <span style={{ fontSize: 10, fontWeight: 600, color: 'var(--blue)', fontFamily: 'DM Mono, monospace', flexShrink: 0 }}>p.{c.page_number}</span>
                        )}
                        <p style={{ fontSize: 12, color: 'var(--text-2)', lineHeight: 1.55 }}>{c.text}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      ))}
    </>
  );
}

export function QAView({ bookId, topicId, topicTitle }: Props) {
  const { qaMessages, qaLoading, error, askQuestion, clearQA } = useStudyStore();
  const [input, setInput] = useState('');
  const [scoped, setScoped] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const el = bottomRef.current?.parentElement;
    if (el) el.scrollTop = el.scrollHeight;
  }, [qaMessages.length, qaLoading]);

  useEffect(() => { clearQA(); }, [topicId]); // eslint-disable-line react-hooks/exhaustive-deps

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const q = input.trim();
    if (!q || qaLoading) return;
    setInput('');
    await askQuestion(bookId, q, scoped ? topicId : null);
    setTimeout(() => inputRef.current?.focus(), 50);
  }

  const suggestions = [
    `What is the main idea of ${topicTitle}?`,
    'Give me a concrete example.',
    'How does this connect to neural networks?',
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 218px)', maxWidth: 660, animation: 'fadeIn 0.2s ease-out' }}>
      {/* Thread */}
      <div style={{ flex: 1, overflow: 'auto', paddingBottom: 16 }}>
        {qaMessages.length === 0 && !qaLoading && (
          <div style={{ paddingBottom: 20 }}>
            <p style={{ fontSize: 14, color: 'var(--text-2)', lineHeight: 1.65, marginBottom: 18 }}>
              Ask anything about <strong style={{ color: 'var(--text)', fontWeight: 600 }}>{topicTitle}</strong>. Responses are grounded in the source text with citations.
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
              {suggestions.map(s => (
                <button key={s} onClick={() => { setInput(s); inputRef.current?.focus(); }}
                  style={{ padding: '9px 13px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--r)', fontSize: 13, color: 'var(--text-2)', cursor: 'pointer', textAlign: 'left', fontFamily: 'inherit', transition: 'all 0.15s' }}
                  onMouseEnter={e => { e.currentTarget.style.background = 'var(--bg)'; e.currentTarget.style.color = 'var(--text)'; }}
                  onMouseLeave={e => { e.currentTarget.style.background = 'var(--surface)'; e.currentTarget.style.color = 'var(--text-2)'; }}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        <Thread messages={qaMessages} />
        {qaLoading && (
          <div style={{ animation: 'fadeIn 0.15s ease-out' }}>
            <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '3px 12px 12px 12px', padding: '9px 14px', display: 'inline-flex', alignItems: 'center', gap: 8 }}>
              <Spinner size={12} color="var(--text-3)" />
              <span style={{ fontSize: 13, color: 'var(--text-3)' }}>Thinking…</span>
            </div>
          </div>
        )}
        {error && <p style={{ fontSize: 13, color: 'var(--rose)', marginTop: 8 }}>Error: {error}</p>}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={{ borderTop: '1px solid var(--border)', paddingTop: 14, flexShrink: 0 }}>
        <form onSubmit={handleSubmit} style={{ display: 'flex', gap: 8, marginBottom: 9 }}>
          <input ref={inputRef} value={input} onChange={e => setInput(e.target.value)}
            placeholder="Ask a question…" disabled={qaLoading}
            style={{ flex: 1, fontSize: 13.5, border: '1px solid var(--border)', borderRadius: 'var(--r)', padding: '10px 13px', background: 'var(--surface)', color: 'var(--text)', outline: 'none', fontFamily: 'inherit', transition: 'border-color 0.15s' }}
            onFocus={e => e.target.style.borderColor = 'oklch(75% 0.08 78)'}
            onBlur={e => e.target.style.borderColor = 'var(--border)'} />
          <button type="submit" disabled={qaLoading || !input.trim()}
            style={{ padding: '10px 16px', background: input.trim() && !qaLoading ? 'var(--text)' : 'var(--border)', color: input.trim() && !qaLoading ? 'white' : 'var(--text-3)', border: 'none', borderRadius: 'var(--r)', fontSize: 13, fontWeight: 500, cursor: input.trim() && !qaLoading ? 'pointer' : 'not-allowed', fontFamily: 'inherit', transition: 'all 0.15s' }}>
            Ask
          </button>
        </form>
        <label style={{ display: 'flex', alignItems: 'center', gap: 7, cursor: 'pointer', userSelect: 'none' }}>
          <input type="checkbox" checked={scoped} onChange={e => setScoped(e.target.checked)} style={{ accentColor: 'var(--amber)', width: 13, height: 13 }} />
          <span style={{ fontSize: 12, color: 'var(--text-3)' }}>Scope answers to this topic</span>
        </label>
      </div>
    </div>
  );
}
