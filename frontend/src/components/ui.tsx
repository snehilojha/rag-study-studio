// Shared UI primitives — Logo, Spinner, Badge, BookCover

export const CHAP_COLORS = [
  'oklch(72% 0.14 75)',
  'oklch(62% 0.14 252)',
  'oklch(65% 0.13 158)',
  'oklch(62% 0.14 290)',
  'oklch(58% 0.15 15)',
];
export const CHAP_BG = [
  'oklch(97.5% 0.022 75)',
  'oklch(97.5% 0.018 252)',
  'oklch(97.5% 0.018 158)',
  'oklch(97.5% 0.018 290)',
  'oklch(97.5% 0.018 15)',
];
export const EDGE_COLORS: Record<string, string> = {
  prerequisite: 'oklch(65% 0.10 40)',
  extension:    'oklch(58% 0.14 252)',
  application:  'oklch(62% 0.13 158)',
  contrast:     'oklch(55% 0.14 0)',
};

export function Spinner({ size = 16, color = 'var(--text-3)' }: { size?: number; color?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 20 20" style={{ animation: 'spin 0.9s linear infinite', flexShrink: 0 }}>
      <circle cx="10" cy="10" r="8" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeDasharray="25 15" />
    </svg>
  );
}

type BadgeStatus = 'ready' | 'processing' | 'pending' | 'failed';
const BADGE_MAP: Record<BadgeStatus, { label: string; color: string; bg: string }> = {
  ready:      { label: 'Ready',      color: 'var(--sage)',  bg: 'var(--sage-bg)' },
  processing: { label: 'Processing', color: 'var(--blue)',  bg: 'var(--blue-bg)' },
  pending:    { label: 'Pending',    color: 'var(--amber)', bg: 'var(--amber-bg)' },
  failed:     { label: 'Failed',     color: 'var(--rose)',  bg: 'var(--rose-bg)' },
};

export function Badge({ status }: { status: string }) {
  const c = BADGE_MAP[status as BadgeStatus] ?? BADGE_MAP.pending;
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '2px 8px', background: c.bg, color: c.color, borderRadius: 'var(--r-sm)', fontSize: 11, fontWeight: 500 }}>
      <span style={{ width: 5, height: 5, borderRadius: '50%', background: c.color, animation: status === 'processing' ? 'pulse 1.4s ease-in-out infinite' : 'none' }} />
      {c.label}
    </span>
  );
}

export function BookCover({ idx = 0 }: { idx?: number }) {
  const col = CHAP_COLORS[idx % CHAP_COLORS.length];
  return (
    <div style={{ width: 48, height: 64, borderRadius: 4, background: col, position: 'relative', overflow: 'hidden', flexShrink: 0 }}>
      {[...Array(9)].map((_, i) => (
        <div key={i} style={{ position: 'absolute', left: 0, right: 0, top: i * 8, height: 1, background: 'oklch(100% 0 0 / 0.13)' }} />
      ))}
      <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 4, background: 'oklch(0% 0 0 / 0.13)' }} />
    </div>
  );
}

export function Logo({ size = 24 }: { size?: number }) {
  return (
    <div style={{ width: size, height: size, borderRadius: Math.round(size * 0.25), background: 'var(--text)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
      <svg width={size * 0.6} height={size * 0.6} viewBox="0 0 16 16" fill="none">
        <rect x="1.5" y="1.5" width="5" height="13" rx="1.2" fill="white" opacity="0.9" />
        <rect x="9" y="1.5" width="5.5" height="7.5" rx="1.2" fill="white" opacity="0.55" />
        <rect x="9" y="11" width="5.5" height="3.5" rx="1.2" fill="white" opacity="0.55" />
      </svg>
    </div>
  );
}
