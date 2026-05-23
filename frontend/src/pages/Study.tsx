import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useBookStore } from '../store/useBookStore';
import { useStudyStore } from '../store/useStudyStore';
import { TheoryView } from '../components/TheoryView';
import { PracticalView } from '../components/PracticalView';
import { QAView } from '../components/QuizView';
import { ConnectedTopics } from '../components/ConnectedTopics';
type Tab = 'theory' | 'practical' | 'qa';
const TABS: { id: Tab; label: string }[] = [
  { id: 'theory',    label: 'Theory' },
  { id: 'practical', label: 'Practical' },
  { id: 'qa',        label: 'Q&A' },
];

function Skeleton() {
  return (
    <div style={{ maxWidth: 660, animation: 'fadeIn 0.2s ease-out' }}>
      {[1, 0.85, 0.7, 1, 0.75].map((w, i) => (
        <div key={i} style={{ height: 14, background: 'var(--border)', borderRadius: 4, width: `${w * 100}%`, marginBottom: 10, animation: 'pulse 1.4s ease-in-out infinite' }} />
      ))}
    </div>
  );
}

export function TopicStudy() {
  const { bookId, topicId } = useParams<{ bookId: string; topicId: string }>();
  const navigate = useNavigate();
  const bId = Number(bookId);
  const tId = Number(topicId);

  const [activeTab, setActiveTab] = useState<Tab>('theory');

  const { books, allTopics, fetchBooks, fetchAllTopics } = useBookStore();
  const { theory, practical, theoryLoading, practicalLoading, fetchTheory, fetchPractical } = useStudyStore();

  useEffect(() => { if (books.length === 0) fetchBooks(); }, []); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { if (allTopics.length === 0) fetchAllTopics(bId); }, [bId]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { fetchTheory(tId); }, [tId]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (activeTab === 'theory') fetchTheory(tId);
    if (activeTab === 'practical') fetchPractical(tId);
  }, [activeTab, tId]); // eslint-disable-line react-hooks/exhaustive-deps

  const book = books.find(b => b.id === bId);
  const topic = allTopics.find(t => t.id === tId);
  const theoryContent = theory[tId];
  const practicalContent = practical[tId];

  // Breadcrumb items
  const crumbs = [
    { label: 'Library', act: () => navigate('/') },
    { label: book?.title ?? 'Book', act: () => navigate(`/books/${bId}`) },
    { label: topic?.chapter_title ?? '', act: undefined as (() => void) | undefined },
  ];

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', animation: 'fadeIn 0.3s ease-out' }}>
      {/* Breadcrumb header */}
      <header style={{ height: 49, display: 'flex', alignItems: 'center', padding: '0 22px', borderBottom: '1px solid var(--border)', background: 'var(--surface)', flexShrink: 0 }}>
        <nav style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 12, color: 'var(--text-3)', flexWrap: 'wrap' }}>
          {crumbs.map((crumb, i) => (
            <span key={i} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
              {crumb.act
                ? <button onClick={crumb.act} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 12, color: 'var(--text-3)', padding: 0, fontFamily: 'inherit', transition: 'color 0.1s' }} onMouseEnter={e => e.currentTarget.style.color = 'var(--text)'} onMouseLeave={e => e.currentTarget.style.color = 'var(--text-3)'}>{crumb.label}</button>
                : <span>{crumb.label}</span>
              }
              <span style={{ opacity: 0.5 }}>›</span>
            </span>
          ))}
          <span style={{ color: 'var(--text)', fontWeight: 500 }}>{topic?.title ?? '…'}</span>
        </nav>
      </header>

      {/* Main layout */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Content area */}
        <div style={{ flex: 1, overflow: 'auto', padding: '26px 30px 32px' }}>
          <h1 style={{ fontSize: 22, fontWeight: 600, letterSpacing: '-0.02em', lineHeight: 1.25, marginBottom: 8 }}>{topic?.title ?? '…'}</h1>
          {topic?.summary && (
            <p style={{ fontSize: 13, color: 'var(--text-3)', lineHeight: 1.6, marginBottom: 22 }}>{topic.summary}</p>
          )}

          {/* Tabs */}
          <div style={{ display: 'flex', borderBottom: '1px solid var(--border)', marginBottom: 26 }}>
            {TABS.map(t => (
              <button key={t.id} onClick={() => setActiveTab(t.id)}
                style={{ padding: '9px 16px', background: 'none', border: 'none', borderBottom: `2px solid ${activeTab === t.id ? 'var(--text)' : 'transparent'}`, marginBottom: -1, fontSize: 13.5, fontWeight: activeTab === t.id ? 600 : 400, color: activeTab === t.id ? 'var(--text)' : 'var(--text-3)', cursor: 'pointer', fontFamily: 'inherit', transition: 'all 0.12s' }}
                onMouseEnter={e => { if (activeTab !== t.id) e.currentTarget.style.color = 'var(--text-2)'; }}
                onMouseLeave={e => { if (activeTab !== t.id) e.currentTarget.style.color = 'var(--text-3)'; }}>
                {t.label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          {activeTab === 'theory' && (
            theoryLoading && !theoryContent ? <Skeleton /> :
            theoryContent ? <TheoryView content={theoryContent} /> :
            <p style={{ fontSize: 13, color: 'var(--text-3)' }}>No theory content yet.</p>
          )}
          {activeTab === 'practical' && (
            practicalLoading && !practicalContent ? <Skeleton /> :
            practicalContent ? <PracticalView content={practicalContent} /> :
            <p style={{ fontSize: 13, color: 'var(--text-3)' }}>No practical content yet.</p>
          )}
          {activeTab === 'qa' && topic && (
            <QAView bookId={bId} topicId={tId} topicTitle={topic.title} />
          )}
        </div>

        {/* Right sidebar */}
        <aside style={{ width: 230, flexShrink: 0, borderLeft: '1px solid var(--border)', padding: '26px 18px', overflow: 'auto' }}>
          <ConnectedTopics topicId={tId} bookId={bId} />
        </aside>
      </div>
    </div>
  );
}
