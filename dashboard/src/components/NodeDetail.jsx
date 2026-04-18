export function NodeDetail({ node, onForget, onReinforce }) {
  if (!node) {
    return (
      <div className="panel panel-muted">
        <h3>Node Detail</h3>
        <p>Select a memory node to inspect its type, importance, and reinforcement controls.</p>
      </div>
    );
  }

  return (
    <div className="panel">
      <div className="eyebrow">{node.entity_type}</div>
      <h3>{node.content}</h3>
      <div className="detail-grid">
        <div>
          <span>Importance</span>
          <strong>{(node.importance || 0).toFixed(3)}</strong>
        </div>
        <div>
          <span>Access count</span>
          <strong>{node.access_count || 0}</strong>
        </div>
        <div>
          <span>Pinned</span>
          <strong>{node.pinned ? "Yes" : "No"}</strong>
        </div>
      </div>
      <div className="actions">
        <button className="primary" onClick={() => onReinforce(node.id)}>
          Reinforce
        </button>
        <button className="ghost" onClick={() => onForget(node.id)}>
          Forget
        </button>
      </div>
    </div>
  );
}
