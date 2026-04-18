import { useEffect, useRef } from "react";
import ForceGraph2D from "react-force-graph-2d";

const TYPE_COLORS = {
  person: "#ff9b71",
  project: "#38b48b",
  decision: "#ffcb77",
  preference: "#ff6b6b",
  fact: "#92a8d1",
  event: "#c77dff",
};

export function MemoryGraph({ graphData, onNodeClick }) {
  const graphRef = useRef(null);

  useEffect(() => {
    if (!graphRef.current) {
      return;
    }
    graphRef.current.d3AlphaDecay(0.03);
  }, [graphData]);

  return (
    <ForceGraph2D
      ref={graphRef}
      graphData={graphData}
      backgroundColor="transparent"
      nodeLabel={(node) => `${node.content} (${(node.importance || 0).toFixed(2)})`}
      nodeColor={(node) => TYPE_COLORS[node.entity_type] || "#9fb3c8"}
      nodeVal={(node) => Math.max(2, (node.importance || 0.2) * 16)}
      linkColor={() => "rgba(211, 224, 242, 0.25)"}
      linkWidth={1}
      onNodeClick={onNodeClick}
      cooldownTicks={80}
      nodeCanvasObject={(node, ctx, globalScale) => {
        const label = node.content?.slice(0, 24) || "Memory";
        const fontSize = Math.max(10, 14 / globalScale);
        ctx.beginPath();
        ctx.arc(node.x, node.y, Math.max(3, (node.importance || 0.2) * 10), 0, 2 * Math.PI);
        ctx.fillStyle = TYPE_COLORS[node.entity_type] || "#9fb3c8";
        ctx.fill();

        ctx.font = `600 ${fontSize}px Space Grotesk, Avenir Next, sans-serif`;
        ctx.fillStyle = "#eff6ff";
        ctx.fillText(label, node.x + 10, node.y + 4);
      }}
    />
  );
}
