// Upload zone component.

import { useRef } from "react";

interface Props {
  onFile: (file: File) => void;
  disabled?: boolean;
}

export function UploadZone({ onFile, disabled }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) onFile(file);
    // reset so same file can be re-uploaded if needed
    e.target.value = "";
  }

  return (
    <div>
      <input
        ref={inputRef}
        type="file"
        accept=".pdf"
        disabled={disabled}
        onChange={handleChange}
        style={{ display: "none" }}
      />
      <button disabled={disabled} onClick={() => inputRef.current?.click()}>
        {disabled ? "Uploading..." : "Upload PDF"}
      </button>
    </div>
  );
}
