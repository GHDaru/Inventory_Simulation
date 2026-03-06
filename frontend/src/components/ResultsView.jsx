import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, BarChart, Bar,
} from 'recharts';

const COLORS = [
  '#4f86c6', '#e07b54', '#56b07b', '#c49ac6',
  '#e0c454', '#54b0e0', '#c65480', '#80c654',
];

function StockChart({ stockHistory }) {
  const productNames = Object.keys(stockHistory);
  const days = stockHistory[productNames[0]]?.length ?? 0;

  const data = Array.from({ length: days }, (_, i) => {
    const row = { day: i + 1 };
    productNames.forEach(name => { row[name] = stockHistory[name][i]; });
    return row;
  });

  return (
    <div className="chart-card">
      <h3>Stock levels over time</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="day" label={{ value: 'Day', position: 'insideBottom', offset: -2 }} />
          <YAxis />
          <Tooltip />
          <Legend />
          {productNames.map((name, i) => (
            <Line key={name} type="monotone" dataKey={name}
              stroke={COLORS[i % COLORS.length]} dot={false} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function DemandChart({ dailyRecords }) {
  const productNames = [...new Set(dailyRecords.map(r => r.name))];

  return productNames.map((productName, pi) => {
    const records = dailyRecords
      .filter(r => r.name === productName)
      .map(r => ({ day: r.day + 1, demand: r.demand, unmet: r.unmet_demand }));

    return (
      <div className="chart-card" key={productName}>
        <h3>Demand vs. unmet demand — {productName}</h3>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={records}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="day" label={{ value: 'Day', position: 'insideBottom', offset: -2 }} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="demand" fill={COLORS[pi % COLORS.length]} name="Demand" />
            <Bar dataKey="unmet" fill="#e05454" name="Unmet demand" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  });
}

function SummaryTable({ dailyRecords }) {
  const productNames = [...new Set(dailyRecords.map(r => r.name))];

  const summary = productNames.map(name => {
    const rows = dailyRecords.filter(r => r.name === name);
    const totalDemand = rows.reduce((s, r) => s + r.demand, 0);
    const totalUnmet = rows.reduce((s, r) => s + r.unmet_demand, 0);
    const stockoutDays = rows.filter(r => r.unmet_demand > 0).length;
    const serviceLevel = totalDemand > 0
      ? (((totalDemand - totalUnmet) / totalDemand) * 100).toFixed(1)
      : '100.0';
    return { name, totalDemand: totalDemand.toFixed(0), totalUnmet: totalUnmet.toFixed(0), stockoutDays, serviceLevel };
  });

  return (
    <div className="chart-card">
      <h3>Summary</h3>
      <table className="summary-table">
        <thead>
          <tr>
            <th>Product</th>
            <th>Total demand</th>
            <th>Total unmet demand</th>
            <th>Stockout days</th>
            <th>Service level (%)</th>
          </tr>
        </thead>
        <tbody>
          {summary.map(row => (
            <tr key={row.name}>
              <td>{row.name}</td>
              <td>{row.totalDemand}</td>
              <td>{row.totalUnmet}</td>
              <td>{row.stockoutDays}</td>
              <td>{row.serviceLevel}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function ResultsView({ results }) {
  if (!results) return null;

  return (
    <div className="results-view">
      <h2>Simulation results — {results.days} days</h2>
      <SummaryTable dailyRecords={results.daily_records} />
      <StockChart stockHistory={results.stock_history} />
      <DemandChart dailyRecords={results.daily_records} />
    </div>
  );
}
