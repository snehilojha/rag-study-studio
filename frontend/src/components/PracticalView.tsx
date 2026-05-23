import { useState } from 'react';
import type { PracticalContent } from '../types';

interface Props {
  content: PracticalContent;
}

export function PracticalView({ content }: Props) {
  const [open, setOpen] = useState<Set<number>>(new Set([0]));
  function tog(i: number) {
    setOpen(p => { const n = new Set(p); n.has(i) ? n.delete(i) : n.add(i); return n; });
  }

  return (
    <div style={{ maxWidth: 660, animation: 'fadeIn 0.2s ease-out' }}>
      <p style={{ fontSize: 14.5, lineHeight: 1.8, color: 'var(--text)', marginBottom: 30 }}>{content.overview}</p>

      {content.examples.length > 0 && (
        <div style={{ marginBottom: 26 }}>
          <p style={{ fontSize: 10.5, fontWeight: 700, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 14 }}>Examples</p>
          <div style={{ border: '1px solid var(--border)', borderRadius: 'var(--r)', overflow: 'hidden' }}>
            {content.examples.map((ex, i) => (
              <div key={i} style={{ borderBottom: i < content.examples.length - 1 ? '1px solid var(--border-s)' : 'none' }}>
                <button onClick={() => tog(i)}
                  style={{ width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '13px 15px', background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left', fontFamily: 'inherit', transition: 'background 0.1s' }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--bg)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'none'}>
                  <span style={{ fontSize: 13.5, fontWeight: 500, color: 'var(--text)' }}>{ex.title}</span>
                  <span style={{ fontSize: 20, color: 'var(--text-3)', fontWeight: 300, lineHeight: 1, flexShrink: 0 }}>{open.has(i) ? '−' : '+'}</span>
                </button>
                {open.has(i) && (
                  <div style={{ padding: '0 15px 15px', animation: 'fadeIn 0.18s ease-out' }}>
                    {ex.description && <p style={{ fontSize: 13, color: 'var(--text-2)', lineHeight: 1.65, marginBottom: 13 }}>{ex.description}</p>}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                      {ex.steps.map((s, si) => (
                        <div key={si} style={{ display: 'flex', gap: 12 }}>
                          <span style={{ fontSize: 10, fontWeight: 700, color: 'var(--blue)', fontFamily: 'DM Mono, monospace', minWidth: 22, paddingTop: 2, flexShrink: 0 }}>{String(si + 1).padStart(2, '0')}</span>
                          <p style={{ fontSize: 13, lineHeight: 1.62, color: 'var(--text)' }}>{s}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {content.tips.length > 0 && (
        <div>
          <p style={{ fontSize: 10.5, fontWeight: 700, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 14 }}>Tips</p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {content.tips.map((tip, i) => (
              <div key={i} style={{ display: 'flex', gap: 10, padding: '10px 13px', background: 'var(--blue-bg)', borderRadius: 'var(--r-sm)', border: '1px solid oklch(91% 0.018 252)' }}>
                <span style={{ color: 'var(--blue)', fontSize: 13, flexShrink: 0, marginTop: 1 }}>→</span>
                <p style={{ fontSize: 13, lineHeight: 1.62, color: 'var(--text)' }}>{tip}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
