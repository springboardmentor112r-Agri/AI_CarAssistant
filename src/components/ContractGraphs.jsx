import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell,
  ResponsiveContainer, Legend, PieChart, Pie,
} from 'recharts';

const COLORS = {
  excellent: '#10b981',
  good: '#3b82f6',
  fair: '#f97316',
  poor: '#ef4444',
};

function scoreColor(score) {
  if (score >= 80) return COLORS.excellent;
  if (score >= 60) return COLORS.good;
  if (score >= 40) return COLORS.fair;
  return COLORS.poor;
}

const SEVERITY_COLORS = { high: '#ef4444', medium: '#f97316', low: '#f59e0b' };

// Custom tooltip for bar chart
function BarTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="graph-tooltip">
      <strong>{d.name}</strong>
      <p>Score: {d.score}/100</p>
      <p>Weight: {d.weight}%</p>
      <p>Contribution: {d.contribution.toFixed(1)} pts</p>
      {d.value !== 'N/A' && <p>Value: {d.value}</p>}
    </div>
  );
}

// Custom tooltip for radar chart
function RadarTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="graph-tooltip">
      <strong>{d.name}</strong>
      <p>Score: {d.score}/100</p>
    </div>
  );
}

export default function ContractGraphs({ breakdown, redFlags }) {
  // Prepare data for charts (only scored items)
  const scored = breakdown.filter((b) => b.score !== null);
  if (scored.length === 0) return null;

  const totalWeight = scored.reduce((s, b) => s + b.weight, 0);

  const radarData = scored.map((b) => ({
    name: b.name,
    score: b.score,
    fullMark: 100,
  }));

  const barData = scored.map((b) => ({
    name: b.name,
    score: b.score,
    weight: b.weight,
    contribution: (b.score * b.weight) / totalWeight,
    value: String(b.value),
  }));

  // Red flags by severity for pie chart
  const severityCounts = { high: 0, medium: 0, low: 0 };
  (redFlags || []).forEach((f) => { severityCounts[f.severity] = (severityCounts[f.severity] || 0) + 1; });
  const pieData = Object.entries(severityCounts)
    .filter(([, v]) => v > 0)
    .map(([sev, count]) => ({ name: sev.charAt(0).toUpperCase() + sev.slice(1), value: count, color: SEVERITY_COLORS[sev] }));

  return (
    <div className="contract-graphs">
      <h4>Visual Analysis</h4>

      <div className="graphs-grid">
        {/* Radar Chart */}
        <div className="graph-card">
          <h5>Criteria Overview</h5>
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={radarData} outerRadius="75%">
              <PolarGrid stroke="#e2e8f0" />
              <PolarAngleAxis dataKey="name" tick={{ fill: '#334155', fontSize: 11 }} />
              <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 10 }} />
              <Tooltip content={<RadarTooltip />} />
              <Radar
                name="Score"
                dataKey="score"
                stroke="#f97316"
                fill="#f97316"
                fillOpacity={0.18}
                strokeWidth={2}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* Horizontal Bar Chart */}
        <div className="graph-card">
          <h5>Score by Criterion</h5>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={barData} layout="vertical" margin={{ left: 20, right: 20, top: 5, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis type="number" domain={[0, 100]} tick={{ fill: '#334155', fontSize: 11 }} />
              <YAxis dataKey="name" type="category" width={110} tick={{ fill: '#334155', fontSize: 11 }} />
              <Tooltip content={<BarTooltip />} />
              <Bar dataKey="score" radius={[0, 6, 6, 0]} barSize={22}>
                {barData.map((entry, i) => (
                  <Cell key={i} fill={scoreColor(entry.score)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Red Flags Pie */}
        {pieData.length > 0 && (
          <div className="graph-card graph-card-small">
            <h5>Red Flags by Severity</h5>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={pieData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={75}
                  paddingAngle={4}
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {pieData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Weight Distribution */}
        <div className="graph-card graph-card-small">
          <h5>Weight Distribution</h5>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={scored.map((b) => ({ name: b.name, value: b.weight }))}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                innerRadius={45}
                outerRadius={75}
                paddingAngle={2}
                label={({ name, value }) => `${value}%`}
              >
                {scored.map((_, i) => (
                  <Cell key={i} fill={['#f97316', '#ea580c', '#3b82f6', '#0f172a', '#1e293b', '#10b981', '#64748b'][i % 7]} />
                ))}
              </Pie>
              <Tooltip formatter={(v, name) => [`${v}%`, name]} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
