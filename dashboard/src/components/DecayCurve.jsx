import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

function importanceAt(initial, hours, pinned) {
  const decayRate = 0.008;
  const projected = initial * Math.exp(-decayRate * hours);
  return pinned ? Math.max(projected, 0.3) : projected;
}

export function DecayCurve({ node }) {
  const baseImportance = node?.importance || 0.7;
  const data = Array.from({ length: 13 }, (_, index) => {
    const hours = index * 12;
    return {
      hours,
      importance: Number(importanceAt(baseImportance, hours, node?.pinned).toFixed(3)),
    };
  });

  return (
    <div className="panel">
      <div className="eyebrow">Decay Preview</div>
      <h3>{node ? "Projected memory retention" : "Default forgetting curve"}</h3>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={data}>
            <XAxis dataKey="hours" stroke="#9fb3c8" />
            <YAxis stroke="#9fb3c8" domain={[0, 1]} />
            <Tooltip />
            <Line type="monotone" dataKey="importance" stroke="#38b48b" strokeWidth={3} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
