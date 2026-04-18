import { useEffect, useMemo, useState } from "react";
import { MemoryGraph } from "./components/MemoryGraph.jsx";
import { NodeDetail } from "./components/NodeDetail.jsx";
import { DecayCurve } from "./components/DecayCurve.jsx";
import { useSSE } from "./hooks/useSSE.js";

const API = "http://localhost:8000";

const emptyGraph = { nodes: [], links: [] };

export default function App() {
  const [graphData, setGraphData] = useState(emptyGraph);
  const [stats, setStats] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [query, setQuery] = useState("");
  const [message, setMessage] = useState("");
  const [context, setContext] = useState("");
  const { data: liveData, status } = useSSE(`${API}/memory/events`);

  useEffect(() => {
    void hydrate();
  }, []);

  useEffect(() => {
    if (!liveData) {
      return;
    }
    setStats(liveData.stats);
    setGraphData(normalizeGraph(liveData.graph));
  }, [liveData]);

  async function hydrate() {
    const [graphResponse, statsResponse] = await Promise.all([
      fetch(`${API}/memory/graph`),
      fetch(`${API}/memory/stats`),
    ]);
    setGraphData(normalizeGraph(await graphResponse.json()));
    setStats(await statsResponse.json());
  }

  async function handleIngest(event) {
    event.preventDefault();
    if (!message.trim()) {
      return;
    }
    await fetch(`${API}/memory/ingest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    setMessage("");
    await hydrate();
  }

  async function handleQuery(event) {
    event.preventDefault();
    if (!query.trim()) {
      return;
    }
    const response = await fetch(`${API}/memory/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, top_k: 8 }),
    });
    const data = await response.json();
    setContext(data.context || "");
  }

  async function handleForget(nodeId) {
    await fetch(`${API}/memory/${nodeId}`, { method: "DELETE" });
    setSelectedNode(null);
    await hydrate();
  }

  async function handleReinforce(nodeId) {
    await fetch(`${API}/memory/${nodeId}/reinforce`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ boost: 0.3 }),
    });
    await hydrate();
  }

  const headlineStats = useMemo(() => {
    if (!stats) {
      return [];
    }
    return [
      { label: "Total memories", value: stats.total_nodes },
      { label: "Average importance", value: stats.avg_importance },
      { label: "Pinned memories", value: stats.pinned },
      { label: "Live feed", value: status },
    ];
  }, [stats, status]);

  return (
    <div className="shell">
      <header className="hero">
        <div>
          <div className="eyebrow">Personal Operating Memory</div>
          <h1>MemOS Dashboard</h1>
          <p>
            Watch memories form a living graph, decay with time, and resurface through retrieval.
          </p>
        </div>
        <div className="stat-row">
          {headlineStats.map((item) => (
            <div className="stat-card" key={item.label}>
              <span>{item.label}</span>
              <strong>{item.value}</strong>
            </div>
          ))}
        </div>
      </header>

      <main className="layout">
        <section className="canvas panel">
          <div className="section-head">
            <div>
              <div className="eyebrow">Memory Graph</div>
              <h2>Relationship topology</h2>
            </div>
          </div>
          <div className="graph-wrap">
            <MemoryGraph graphData={graphData} onNodeClick={setSelectedNode} />
          </div>
        </section>

        <aside className="sidebar">
          <form className="panel" onSubmit={handleIngest}>
            <div className="eyebrow">Ingest</div>
            <h3>Feed the memory layer</h3>
            <textarea
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="Example: !remember MemOS should feel like a second brain for LLMs."
              rows={5}
            />
            <button className="primary" type="submit">
              Store memory
            </button>
          </form>

          <form className="panel" onSubmit={handleQuery}>
            <div className="eyebrow">Retrieve</div>
            <h3>Ask the graph</h3>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="What should the assistant remember?"
            />
            <button className="primary" type="submit">
              Build context
            </button>
            <pre className="context-box">{context || "Retrieved context will appear here."}</pre>
          </form>

          <NodeDetail node={selectedNode} onForget={handleForget} onReinforce={handleReinforce} />
          <DecayCurve node={selectedNode} />
        </aside>
      </main>
    </div>
  );
}

function normalizeGraph(data) {
  return {
    nodes: (data.nodes || []).map((node) => ({
      ...node,
      id: node.id,
    })),
    links: (data.links || []).map((link, index) => ({
      ...link,
      id: `${link.source}-${link.target}-${index}`,
    })),
  };
}
