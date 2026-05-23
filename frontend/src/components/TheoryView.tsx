import type { TheoryContent } from '../types';

interface Props {
  content: TheoryContent;
}

export function TheoryView({ content }: Props) {
  return (
    <div style={{ maxWidth: 660, animation: 'fadeIn 0.2s ease-out' }}>
      {/* Explanation */}
      {content.explanation.split('\n\n').map((para, i, arr) => (
        <p key={i} style={{ fontSize: 14.5, lineHeight: 1.8, color: 'var(--text)', marginBottom: i < arr.length - 1 ? 16 : 0 }}>
          {para.trim()}
        </p>
      ))}

      {/* Key points */}
      {content.key_points.length > 0 && (
        <div style={{ margin: '30px 0' }}>
          <p style={{ fontSize: 10.5, fontWeight: 700, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 14 }}>Key Points</p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {content.key_points.map((pt, i) => (
              <div key={i} style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                <div style={{ width: 20, height: 20, borderRadius: 5, background: 'var(--amber-bg)', border: '1px solid oklch(90% 0.04 75)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: 2 }}>
                  <span style={{ fontSize: 10, fontWeight: 700, color: 'var(--amber)' }}>{i + 1}</span>
                </div>
                <p style={{ fontSize: 13.5, lineHeight: 1.65, color: 'var(--text)' }}>{pt}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Definitions */}
      {content.definitions.length > 0 && (
        <div>
          <p style={{ fontSize: 10.5, fontWeight: 700, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 14 }}>Definitions</p>
          <div style={{ border: '1px solid var(--border)', borderRadius: 'var(--r)', overflow: 'hidden' }}>
            {content.definitions.map((d, i) => (
              <div key={i} style={{ display: 'grid', gridTemplateColumns: '175px 1fr', borderBottom: i < content.definitions.length - 1 ? '1px solid var(--border-s)' : 'none' }}>
                <div style={{ padding: '12px 14px', background: 'var(--bg)', borderRight: '1px solid var(--border-s)' }}>
                  <span style={{ fontSize: 12, fontWeight: 600, fontFamily: 'DM Mono, monospace', color: 'var(--text)' }}>{d.term}</span>
                </div>
                <div style={{ padding: '12px 14px' }}>
                  <p style={{ fontSize: 13, lineHeight: 1.62, color: 'var(--text-2)' }}>{d.definition}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
