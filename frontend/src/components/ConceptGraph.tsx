import { useMemo, useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { CHAP_COLORS, CHAP_BG, EDGE_COLORS } from './ui';
import type { Topic, Connection } from '../types';

interface Props {
  topics: Topic[];
  connections: Connection[];
  bookId: number;
  activeTopic?: number | null;
}

function computePositions(topics: Topic[], w: number, h: number): Record<number, { x: number; y: number }> {
  const byChapter = new Map<number, Topic[]>();
  topics.forEach(t => {
    if (!byChapter.has(t.chapter_order_index)) byChapter.set(t.chapter_order_index, []);
    byChapter.get(t.chapter_order_index)!.push(t);
  });
  const cols = Array.from(byChapter.entries()).sort(([a], [b]) => a - b);
  const n = cols.length;
  const px = 80, py = 60;
  const pos: Record<number, { x: number; y: number }> = {};
  cols.forEach(([, colTopics], ci) => {
    const x = n > 1 ? px + (ci / (n - 1)) * (w - px * 2) : w / 2;
    const sorted = [...colTopics].sort((a, b) => a.order_index - b.order_index);
    const m = sorted.length;
    sorted.forEach((t, ti) => {
      const y = m > 1 ? py + (ti / (m - 1)) * (h - py * 2) : h / 2;
      // stagger even columns down slightly for visual variety
      pos[t.id] = { x, y: y + (ci % 2 === 1 ? 20 : 0) };
    });
  });
  return pos;
}

export function ConceptGraph({ topics, connections, bookId, activeTopic }: Props) {
  const navigate = useNavigate();
  const containerRef = useRef<HTMLDivElement>(null);
  const [sz, setSz] = useState({ w: 0, h: 0 });
  const [hov, setHov] = useState<number | null>(null);

  useEffect(() => {
    const obs = new ResizeObserver(([e]) => setSz({ w: e.contentRect.width, h: e.contentRect.height }));
    if (containerRef.current) obs.observe(containerRef.current);
    return () => obs.disconnect();
  }, []);

  const pos = useMemo(() => sz.w > 0 ? computePositions(topics, sz.w, sz.h) : {}, [topics, sz]);

  // Derive unique chapters for legend
  const chapters = useMemo(() => {
    const seen = new Map<number, { order: number; title: string }>();
    topics.forEach(t => {
      if (!seen.has(t.chapter_order_index)) seen.set(t.chapter_order_index, { order: t.chapter_order_index, title: t.chapter_title });
    });
    return Array.from(seen.values()).sort((a, b) => a.order - b.order);
  }, [topics]);

  return (
    <div ref={containerRef} style={{ width: '100%', height: '100%', position: 'relative', overflow: 'hidden' }}>
      {topics.length === 0 && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', fontSize: 13, color: 'var(--text-3)' }}>
          No topics found.
        </div>
      )}
      {topics.length > 0 && sz.w > 0 && (
        <svg width={sz.w} height={sz.h} style={{ position: 'absolute', inset: 0 }}>
          <defs>
            {Object.entries(EDGE_COLORS).map(([type, color]) => (
              <marker key={type} id={`arr-${type}`} viewBox="0 0 10 10" refX="23" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                <path d="M0 0L10 5L0 10z" fill={color} opacity="0.75" />
              </marker>
            ))}
          </defs>

          {/* Edges */}
          {connections.map(c => {
            const s = pos[c.source_topic_id], t = pos[c.target_topic_id];
            if (!s || !t) return null;
            const lit = hov != null && (c.source_topic_id === hov || c.target_topic_id === hov);
            const mx = (s.x + t.x) / 2, my = (s.y + t.y) / 2 - 26;
            const col = EDGE_COLORS[c.edge_type] ?? EDGE_COLORS.extension;
            return (
              <path key={c.id}
                d={`M${s.x} ${s.y} Q${mx} ${my} ${t.x} ${t.y}`}
                stroke={col} strokeWidth={lit ? 2.5 : 1.5}
                strokeOpacity={lit ? 0.9 : 0.32} fill="none"
                strokeDasharray={c.edge_type === 'contrast' ? '5,4' : 'none'}
                markerEnd={`url(#arr-${c.edge_type})`}
                style={{ transition: 'stroke-opacity 0.2s' }}
              />
            );
          })}

          {/* Nodes */}
          {topics.map(t => {
            const p = pos[t.id]; if (!p) return null;
            const ci = (t.chapter_order_index || 1) - 1;
            const col = CHAP_COLORS[ci % CHAP_COLORS.length];
            const bg  = CHAP_BG[ci % CHAP_BG.length];
            const isH = hov === t.id, isA = activeTopic === t.id;
            const r = isA ? 22 : isH ? 20 : 17;
            return (
              <g key={t.id} transform={`translate(${p.x},${p.y})`}
                onClick={() => navigate(`/books/${bookId}/topics/${t.id}`)}
                onMouseEnter={() => setHov(t.id)}
                onMouseLeave={() => setHov(null)}
                style={{ cursor: 'pointer' }}>
                {isA && <circle r={r + 8} fill={col} opacity={0.12} />}
                <circle r={r} fill={isA ? col : bg} stroke={col} strokeWidth={isA ? 2.5 : isH ? 2 : 1.5} style={{ transition: 'all 0.18s ease' }} />
                <text textAnchor="middle" dominantBaseline="central" fill={isA ? 'white' : col}
                  style={{ fontSize: 10, fontWeight: 700, fontFamily: 'DM Sans, sans-serif', userSelect: 'none' }}>
                  {t.title.charAt(0)}
                </text>
                <text y={r + 14} textAnchor="middle" fill={(isH || isA) ? 'var(--text)' : 'var(--text-2)'}
                  style={{ fontSize: 10, fontFamily: 'DM Sans, sans-serif', fontWeight: (isH || isA) ? 600 : 400, userSelect: 'none', transition: 'fill 0.15s' }}>
                  {t.title.length > 22 ? t.title.slice(0, 20) + '…' : t.title}
                </text>
              </g>
            );
          })}
        </svg>
      )}

      {/* Relationship legend */}
      <div style={{ position: 'absolute', bottom: 16, left: 16, background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--r)', padding: '10px 14px', boxShadow: 'var(--shadow)' }}>
        <p style={{ fontSize: 9.5, fontWeight: 700, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>Relationships</p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
          {Object.entries(EDGE_COLORS).map(([type, col]) => (
            <div key={type} style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
              <div style={{ width: 20, height: 2, background: col, borderRadius: 1 }} />
              <span style={{ fontSize: 11, color: 'var(--text-2)', textTransform: 'capitalize' }}>{type}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Chapter legend */}
      {chapters.length > 0 && (
        <div style={{ position: 'absolute', bottom: 16, right: 16, background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--r)', padding: '10px 14px', boxShadow: 'var(--shadow)' }}>
          <p style={{ fontSize: 9.5, fontWeight: 700, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>Chapters</p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
            {chapters.map((ch, i) => (
              <div key={ch.order} style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                <div style={{ width: 8, height: 8, borderRadius: '50%', background: CHAP_COLORS[i % CHAP_COLORS.length], flexShrink: 0 }} />
                <span style={{ fontSize: 11, color: 'var(--text-2)' }}>{ch.order}. {ch.title}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Hint when no connections yet */}
      {connections.length === 0 && (
        <div style={{ position: 'absolute', bottom: 24, left: '50%', transform: 'translateX(-50%)', fontSize: 12, color: 'var(--text-3)', pointerEvents: 'none', whiteSpace: 'nowrap' }}>
          Connections appear as you browse topics
        </div>
      )}
    </div>
  );
}
