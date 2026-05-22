import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useStudyStore } from "../store/useStudyStore";

const BADGE_LABEL: Record<string, string> = {
  prerequisite: "prerequisite",
  extension: "extension",
  application: "application",
  contrast: "contrast",
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

  return (
    <aside className="w-[240px] shrink-0 border-l border-[#E4E4E4] pl-6 space-y-3">
      <h3 className="text-xs font-semibold text-[#555] uppercase tracking-wide">
        Connected Topics
      </h3>

      {connectionsLoading && connections.length === 0 && (
        <p className="text-xs text-[#aaa]">Loading…</p>
      )}

      {!connectionsLoading && connections.length === 0 && (
        <p className="text-xs text-[#aaa]">No connections found for this topic.</p>
      )}

      <ul className="space-y-3">
        {connections
          .filter((c) => c.valid)
          .map((conn, i) => (
            <li key={i}>
              <button
                onClick={() => navigate(`/books/${bookId}/topics/${conn.target_topic_id}`)}
                className="w-full text-left group space-y-1"
              >
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs font-medium text-[#111] group-hover:underline">
                    → {conn.target_topic}
                  </span>
                  <span className="text-xs px-1.5 py-0.5 bg-[#F0F0F0] text-[#555] rounded">
                    {BADGE_LABEL[conn.relationship] ?? conn.relationship}
                  </span>
                </div>
                {conn.reason && (
                  <p className="text-xs text-[#888] leading-relaxed">{conn.reason}</p>
                )}
              </button>
            </li>
          ))}
      </ul>
    </aside>
  );
}
