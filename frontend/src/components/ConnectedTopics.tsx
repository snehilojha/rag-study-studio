import { useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useStudyStore } from '../store/useStudyStore';
import { CHAP_COLORS } from './ui';

const BADGE_STYLE: Record<string, { color: string; bg: string }> = {
  prerequisite: { color: 'oklch(62% 0.12 40)', bg: 'oklch(97.5% 0.018 40)' },
  extension:    { color: 'var(--blue)',  bg: 'var(--blue-bg)' },
  application:  { color: 'var(--sage)',  bg: 'var(--sage-bg)' },
  contrast:     { color: 'var(--rose)',  bg: 'var(--rose-bg)' },
};

interface Props {
  topicId: number;
  bookId: number;
}

export function ConnectedTopics({ topicId, bookId }: Props) {
  const navigate = useNavigate();
  const { topicConnections, connectionsLoading, fetchTopicConnections } = useStudyStore();

  useEffect(() => {
    fetchTopicConnections(topicId);
  }, [topicId]); // eslint-disable-line react-hooks/exhaustive-deps

  const connections = topicConnections[topicId] ?? [];
  const valid = useMemo(() => connections.filter(c => c.valid), [connections]);

  return (
    <div>
      <p style={{ fontSize: 10.5, fontWeight: 700, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 16 }}>Connected Topics</p>

      {connectionsLoading && valid.length === 0 && (
        <p style={{ fontSize: 12, color: 'var(--text-3)' }}>Loading…</p>
      )}
      {!connectionsLoading && valid.length === 0 && (
        <p style={{ fontSize: 12, color: 'var(--text-3)' }}>No connections for this topic.</p>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        {valid.map((c, i) => {
          const bd = BADGE_STYLE[c.relationship] ?? BADGE_STYLE.extension;
          // use target topic id for color — pick a color index based on topic id
          const ci = (c.target_topic_id % CHAP_COLORS.length);
          return (
            <button key={i} onClick={() => navigate(`/books/${bookId}/topics/${c.target_topic_id}`)}
              style={{ background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left', padding: 0 }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 6, marginBottom: 5 }}>
                <div style={{ width: 6, height: 6, borderRadius: '50%', background: CHAP_COLORS[ci], flexShrink: 0, marginTop: 5 }} />
                <span style={{ fontSize: 12.5, fontWeight: 500, lineHeight: 1.4, color: 'var(--text)' }}
                  onMouseEnter={e => e.currentTarget.style.textDecoration = 'underline'}
                  onMouseLeave={e => e.currentTarget.style.textDecoration = 'none'}>
                  {c.target_topic}
                </span>
              </div>
              <span style={{ fontSize: 10.5, fontWeight: 500, color: bd.color, background: bd.bg, padding: '2px 7px', borderRadius: 4, textTransform: 'capitalize', marginLeft: 12, display: 'inline-block' }}>
                {c.relationship}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
