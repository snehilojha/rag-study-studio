import { useEffect, useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useBookStore } from '../store/useBookStore';
import { ConceptGraph } from '../components/ConceptGraph';
import { CHAP_COLORS } from '../components/ui';

export function BookMap() {
  const { bookId } = useParams<{ bookId: string }>();
  const navigate = useNavigate();
  const id = Number(bookId);

  const { books, chapters, allTopics, connections, isLoading, fetchBooks, selectBook, fetchAllTopics, fetchBookConnections } = useBookStore();
  const book = books.find(b => b.id === id) ?? null;
  const [openChapters, setOpenChapters] = useState<Set<number>>(new Set([1]));

  useEffect(() => { if (books.length === 0) fetchBooks(); }, []); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!book) return;
    selectBook(book);
    fetchAllTopics(id);
    fetchBookConnections(id);
  }, [id]); // eslint-disable-line react-hooks/exhaustive-deps

  const topicsByChapter = useMemo(() => {
    const m = new Map<number, typeof allTopics>();
    for (const t of allTopics) {
      if (!m.has(t.chapter_id)) m.set(t.chapter_id, []);
      m.get(t.chapter_id)!.push(t);
    }
    return m;
  }, [allTopics]);

  function toggleChapter(id: number) {
    setOpenChapters(p => { const n = new Set(p); n.has(id) ? n.delete(id) : n.add(id); return n; });
  }

  return (
    <div style={{ height: '100vh', display: 'flex', animation: 'fadeIn 0.3s ease-out' }}>
      {/* Sidebar */}
      <aside style={{ width: 272, flexShrink: 0, background: 'var(--surface)', borderRight: '1px solid var(--border)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div style={{ padding: '14px 16px', borderBottom: '1px solid var(--border)' }}>
          <button onClick={() => navigate('/')}
            style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 12, color: 'var(--text-3)', display: 'flex', alignItems: 'center', gap: 4, padding: 0, marginBottom: 10, fontFamily: 'inherit', transition: 'color 0.1s' }}
            onMouseEnter={e => e.currentTarget.style.color = 'var(--text)'}
            onMouseLeave={e => e.currentTarget.style.color = 'var(--text-3)'}>
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><path d="M8 2L4 6l4 4" /></svg>
            Library
          </button>
          <p style={{ fontSize: 14, fontWeight: 600, letterSpacing: '-0.01em', lineHeight: 1.3 }}>{book?.title ?? 'Loading…'}</p>
          <p style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 2 }}>{book?.author}</p>
        </div>

        {/* Stats row */}
        <div style={{ padding: '7px 16px', borderBottom: '1px solid var(--border-s)', display: 'flex', gap: 16 }}>
          {[`${chapters.length} chapters`, `${allTopics.length} topics`, `${connections.length} connections`].map(s => (
            <span key={s} style={{ fontSize: 11, color: 'var(--text-3)' }}>{s}</span>
          ))}
        </div>

        {/* Chapter accordion */}
        <nav style={{ flex: 1, overflow: 'auto', paddingTop: 6 }}>
          {isLoading && chapters.length === 0 && (
            <p style={{ padding: '12px 16px', fontSize: 12, color: 'var(--text-3)' }}>Loading…</p>
          )}
          {chapters.map((ch, i) => {
            const topics = (topicsByChapter.get(ch.id) ?? []).slice().sort((a, b) => a.order_index - b.order_index);
            const isOpen = openChapters.has(ch.id);
            return (
              <div key={ch.id}>
                <button onClick={() => toggleChapter(ch.id)}
                  style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 8, padding: '7px 16px', background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left', fontFamily: 'inherit', transition: 'background 0.1s' }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--bg)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'none'}>
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: CHAP_COLORS[i % CHAP_COLORS.length], flexShrink: 0 }} />
                  <span style={{ flex: 1, fontSize: 12, fontWeight: 500, lineHeight: 1.3 }}>{ch.order_index}. {ch.title}</span>
                  <span style={{ fontSize: 13, color: 'var(--text-3)', lineHeight: 1 }}>{isOpen ? '−' : '+'}</span>
                </button>
                {isOpen && topics.map(t => (
                  <button key={t.id} onClick={() => navigate(`/books/${id}/topics/${t.id}`)}
                    style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '5px 16px 5px 30px', background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left', fontFamily: 'inherit', transition: 'background 0.1s' }}
                    onMouseEnter={e => e.currentTarget.style.background = 'var(--bg)'}
                    onMouseLeave={e => e.currentTarget.style.background = 'none'}>
                    <span style={{ fontSize: 12, color: 'var(--text-2)', lineHeight: 1.3 }}>{t.title}</span>
                    <span style={{ fontSize: 10.5, color: 'var(--text-3)', fontFamily: 'DM Mono, monospace', flexShrink: 0, marginLeft: 8 }}>p.{t.start_page}</span>
                  </button>
                ))}
              </div>
            );
          })}
        </nav>
      </aside>

      {/* Graph area */}
      <main style={{ flex: 1, position: 'relative', overflow: 'hidden', background: 'var(--bg)' }}>
        <div style={{ position: 'absolute', top: 14, left: '50%', transform: 'translateX(-50%)', zIndex: 10, pointerEvents: 'none' }}>
          <p style={{ fontSize: 12, color: 'var(--text-3)', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 100, padding: '4px 14px', whiteSpace: 'nowrap' }}>
            Click any topic node to study it
          </p>
        </div>
        {isLoading
          ? <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', fontSize: 13, color: 'var(--text-3)' }}>Loading…</div>
          : <ConceptGraph topics={allTopics} connections={connections} bookId={id} />
        }
      </main>
    </div>
  );
}
