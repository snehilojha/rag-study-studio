import { useRef, useState } from 'react';
import { Spinner } from './ui';

interface Props {
  onFile: (file: File) => void;
  uploading?: boolean;
}

export function UploadZone({ onFile, uploading }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [drag, setDrag] = useState(false);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) onFile(file);
    e.target.value = '';
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDrag(false);
    if (uploading) return;
    const file = e.dataTransfer.files?.[0];
    if (file?.type === 'application/pdf') onFile(file);
  }

  return (
    <div
      onClick={() => !uploading && inputRef.current?.click()}
      onDragOver={e => { e.preventDefault(); setDrag(true); }}
      onDragLeave={() => setDrag(false)}
      onDrop={handleDrop}
      style={{
        display: 'flex', alignItems: 'center', gap: 14,
        padding: '15px 18px',
        border: `1.5px dashed ${drag ? 'var(--text)' : 'var(--border)'}`,
        borderRadius: 'var(--r)',
        cursor: uploading ? 'default' : 'pointer',
        background: drag ? 'var(--bg-2)' : 'transparent',
        transition: 'all 0.2s', marginBottom: 22,
      }}
    >
      <input ref={inputRef} type="file" accept=".pdf" style={{ display: 'none' }} onChange={handleChange} />
      <div style={{ width: 36, height: 36, borderRadius: 8, background: 'var(--surface)', border: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
        {uploading
          ? <Spinner size={14} color="var(--amber)" />
          : (
            <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="var(--text-3)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M7.5 10V3M7.5 3L5 5.5M7.5 3L10 5.5" /><path d="M2 10.5v2a1 1 0 001 1h9a1 1 0 001-1v-2" />
            </svg>
          )}
      </div>
      <div>
        <p style={{ fontSize: 13, fontWeight: 500, marginBottom: 2 }}>{uploading ? 'Processing book…' : 'Upload a PDF'}</p>
        <p style={{ fontSize: 12, color: 'var(--text-3)' }}>{uploading ? 'Extracting chapters and topics' : 'Drag & drop or click to browse'}</p>
      </div>
    </div>
  );
}
