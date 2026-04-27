// Chapter list component.

import type { Chapter } from "../types";

interface Props {
  chapters: Chapter[];
  onSelect: (chapter: Chapter) => void;
}

export function ChapterList({ chapters, onSelect }: Props) {
  if (chapters.length === 0) return <p>No chapters found.</p>;

  return (
    <ul>
      {chapters.map((chapter) => (
        <li key={chapter.id}>
          <button onClick={() => onSelect(chapter)}>
            {chapter.order_index}. {chapter.title}
            <span> (pages {chapter.start_page}–{chapter.end_page})</span>
          </button>
        </li>
      ))}
    </ul>
  );
}
