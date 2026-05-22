import { useMemo, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  ReactFlow,
  Background,
  Controls,
  Handle,
  Position,
  type Node,
  type Edge,
  type NodeProps,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import type { Topic, Connection } from "../types";

// Layout constants
const NODE_WIDTH = 172;
const NODE_HEIGHT = 44;
const NODE_GAP = 10;
const COLUMN_WIDTH = 200;
const COLUMN_GAP = 72;
const HEADER_HEIGHT = 44;

// Edge stroke styles per relationship type
const EDGE_STYLE: Record<string, React.CSSProperties> = {
  prerequisite: { stroke: "#999", strokeWidth: 1.5, strokeDasharray: "6 3" },
  extension:    { stroke: "#999", strokeWidth: 1 },
  application:  { stroke: "#777", strokeWidth: 2 },
  contrast:     { stroke: "#999", strokeWidth: 1.5, strokeDasharray: "2 5" },
};

// ---------------------------------------------------------------------------
// Custom node: topic
// ---------------------------------------------------------------------------

type TopicData = { label: string; color: string; topicId: number; bookId: number };

function TopicNode({ data }: NodeProps) {
  const navigate = useNavigate();
  const d = data as TopicData;
  return (
    <>
      <Handle type="target" position={Position.Left} style={{ opacity: 0, pointerEvents: "none" }} />
      <div
        onClick={() => navigate(`/books/${d.bookId}/topics/${d.topicId}`)}
        style={{ backgroundColor: d.color, width: NODE_WIDTH, height: NODE_HEIGHT, borderColor: "#D8D8D8" }}
        className="flex items-center px-3 border rounded cursor-pointer hover:border-[#999] transition-colors"
      >
        <span className="text-xs text-[#111] truncate leading-tight">{d.label}</span>
      </div>
      <Handle type="source" position={Position.Right} style={{ opacity: 0, pointerEvents: "none" }} />
    </>
  );
}

// ---------------------------------------------------------------------------
// Custom node: chapter column header
// ---------------------------------------------------------------------------

type HeaderData = { label: string };

function ChapterHeader({ data }: NodeProps) {
  const d = data as HeaderData;
  return (
    <div
      style={{ width: NODE_WIDTH, height: HEADER_HEIGHT }}
      className="flex items-center justify-center"
    >
      <span className="text-xs font-semibold text-[#555] text-center truncate px-1 leading-tight">
        {d.label}
      </span>
    </div>
  );
}

const nodeTypes = { topic: TopicNode, chapterHeader: ChapterHeader };

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

interface Props {
  topics: Topic[];
  connections: Connection[];
  bookId: number;
}

interface Tooltip {
  x: number;
  y: number;
  edgeType: string;
}

export function ConceptGraph({ topics, connections, bookId }: Props) {
  const [tooltip, setTooltip] = useState<Tooltip | null>(null);

  // Group topics into chapter columns, sorted by chapter order
  const columns = useMemo(() => {
    const map = new Map<number, { title: string; topics: Topic[] }>();
    for (const t of topics) {
      if (!map.has(t.chapter_order_index)) {
        map.set(t.chapter_order_index, { title: t.chapter_title, topics: [] });
      }
      map.get(t.chapter_order_index)!.topics.push(t);
    }
    return Array.from(map.entries())
      .sort(([a], [b]) => a - b)
      .map(([, v]) => v);
  }, [topics]);

  const { nodes, edges } = useMemo(() => {
    const nodes: Node[] = [];
    const edges: Edge[] = [];
    const n = columns.length;

    columns.forEach((col, colIdx) => {
      const x = colIdx * (COLUMN_WIDTH + COLUMN_GAP);
      const hue = n > 1 ? Math.round((360 / n) * colIdx) : 200;
      const color = `hsl(${hue}, 10%, 92%)`;

      nodes.push({
        id: `header-${colIdx}`,
        type: "chapterHeader",
        position: { x, y: 0 },
        data: { label: col.title },
        draggable: false,
        selectable: false,
        connectable: false,
      });

      const sorted = [...col.topics].sort((a, b) => a.order_index - b.order_index);
      sorted.forEach((topic, tIdx) => {
        nodes.push({
          id: String(topic.id),
          type: "topic",
          position: { x, y: HEADER_HEIGHT + tIdx * (NODE_HEIGHT + NODE_GAP) },
          data: { label: topic.title, color, topicId: topic.id, bookId },
          draggable: false,
          connectable: false,
        });
      });
    });

    connections.forEach((conn) => {
      edges.push({
        id: `e-${conn.id}`,
        source: String(conn.source_topic_id),
        target: String(conn.target_topic_id),
        type: "smoothstep",
        style: EDGE_STYLE[conn.edge_type] ?? { stroke: "#999", strokeWidth: 1 },
        data: { edgeType: conn.edge_type },
      });
    });

    return { nodes, edges };
  }, [columns, connections, bookId]);

  const onEdgeMouseEnter = useCallback((event: React.MouseEvent, edge: Edge) => {
    setTooltip({ x: event.clientX, y: event.clientY, edgeType: String(edge.data?.edgeType ?? "") });
  }, []);

  const onEdgeMouseLeave = useCallback(() => setTooltip(null), []);

  if (topics.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-sm text-[#888]">
        No topics found.
      </div>
    );
  }

  return (
    <div className="relative w-full h-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.15 }}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        onEdgeMouseEnter={onEdgeMouseEnter}
        onEdgeMouseLeave={onEdgeMouseLeave}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#E4E4E4" gap={24} size={1} />
        <Controls showInteractive={false} />
      </ReactFlow>

      {connections.length === 0 && (
        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 text-xs text-[#aaa] pointer-events-none whitespace-nowrap">
          Connections appear as you browse topics
        </div>
      )}

      {tooltip && (
        <div
          className="fixed z-50 pointer-events-none text-xs bg-white border border-[#E4E4E4] px-2 py-1 rounded"
          style={{ left: tooltip.x + 12, top: tooltip.y - 28 }}
        >
          {tooltip.edgeType}
        </div>
      )}
    </div>
  );
}
