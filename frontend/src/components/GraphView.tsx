import React from "react";
import ForceGraph2D, { ForceGraphMethods } from "react-force-graph-2d";

export type GraphNode = {
  id: string;
  label?: string;
  type?: string;
  [key: string]: any;
};

export type GraphLink = {
  source: string;
  target: string;
  type?: string;
  [key: string]: any;
};

type GraphViewProps = {
  nodes: GraphNode[];
  links: GraphLink[];
  /** Height in px – container will be full width */
  height?: number;
};

const typeColor = (type?: string): string => {
  switch (type) {
    case "weekly_scan":
    case "monthly_web_scan":
    case "dept_scan":
      return "#38bdf8"; // sky
    case "weekly_host":
    case "dept_host":
      return "#22c55e"; // green
    case "weekly_service":
    case "dept_service":
      return "#a855f7"; // purple
    case "weekly_vuln":
    case "monthly_web_vuln":
    case "dept_vuln":
      return "#f97316"; // orange
    case "weekly_observation":
    case "monthly_web_observation":
    case "dept_observation":
      return "#e5e7eb"; // gray
    case "monthly_web_app":
    case "dept":
      return "#facc15"; // yellow
    default:
      return "#e5e7eb";
  }
};

const GraphView: React.FC<GraphViewProps> = ({
  nodes,
  links,
  height = 380,
}) => {
  const fgRef = React.useRef<ForceGraphMethods>();
  const containerRef = React.useRef<HTMLDivElement | null>(null);
  const [dimensions, setDimensions] = React.useState({
    width: 600,
    height,
  });

  // Make graph fill the container width and given height
  React.useLayoutEffect(() => {
    const updateSize = () => {
      if (!containerRef.current) return;
      setDimensions({
        width: containerRef.current.clientWidth,
        height,
      });
    };
    updateSize();
    window.addEventListener("resize", updateSize);
    return () => window.removeEventListener("resize", updateSize);
  }, [height]);

  // Zoom to fit once the force simulation finishes
  const handleEngineStop = React.useCallback(() => {
    if (!fgRef.current || !nodes.length) return;
    fgRef.current.zoomToFit(400, 40);
  }, [nodes.length]);

  return (
    <div
      ref={containerRef}
      style={{ height }}
      className="w-full rounded-lg border border-slate-800 bg-slate-950/70"
    >
      <ForceGraph2D
        ref={fgRef as any}
        width={dimensions.width}
        height={dimensions.height}
        graphData={{ nodes, links }}
        onEngineStop={handleEngineStop}
        // interaction controls
        enableZoomPanInteraction={true}
        enableNodeDrag={true}
        nodeLabel={(node: any) =>
          `${node.label || node.id} (${node.type || "node"})`
        }
        nodeRelSize={6}
        nodeCanvasObject={(node: any, ctx, globalScale) => {
          const label = node.label || node.id;
          const fontSize = 12 / globalScale;
          const color = typeColor(node.type);
          const radius = 4;

          ctx.beginPath();
          ctx.arc(node.x!, node.y!, radius, 0, 2 * Math.PI, false);
          ctx.fillStyle = color;
          ctx.fill();

          ctx.font = `${fontSize}px system-ui`;
          ctx.textAlign = "left";
          ctx.textBaseline = "middle";
          ctx.fillStyle = "#e5e7eb";
          ctx.fillText(label, node.x! + 6, node.y!);
        }}
        linkColor={() => "#64748b"}
        linkDirectionalArrowLength={4}
        linkDirectionalArrowRelPos={0.9}
      />
    </div>
  );
};

export default GraphView;
