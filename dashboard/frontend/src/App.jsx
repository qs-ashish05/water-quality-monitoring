import { useEffect, useMemo, useState } from 'react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { DEFAULT_WINDOW, PARAMS, REFRESH_MS, WINDOW_OPTIONS, isSafe } from './config';

// --------------------------------------------------------------- helpers ---
const fmtTime = (iso) => new Date(iso).toLocaleTimeString('en-IN', { hour12: false });
const fmtNum = (v, d = 2) => (v === null || v === undefined ? '—' : Number(v).toFixed(d));

function average(rows, key) {
  const vals = rows.map((r) => r[key]).filter((v) => v !== null && v !== undefined);
  return vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : null;
}

// ------------------------------------------------------------ data hook ---
// Re-reads the latest `windowSize` rows every REFRESH_MS, so the window slides
// forward as new rows are inserted into the database.
function useReadings(windowSize) {
  const [rows, setRows] = useState([]);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    let controller = null;

    async function load() {
      controller?.abort();
      controller = new AbortController();
      try {
        const res = await fetch(`/api/readings?limit=${windowSize}`, {
          signal: controller.signal,
        });
        if (!res.ok) throw new Error(`API responded with status ${res.status}`);
        const data = await res.json();
        if (!cancelled) {
          setRows(data);
          setError(null);
          setLastUpdated(new Date());
        }
      } catch (err) {
        if (err.name !== 'AbortError' && !cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    const id = setInterval(load, REFRESH_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
      controller?.abort();
    };
  }, [windowSize]);

  return { rows, error, lastUpdated, loading };
}

// ------------------------------------------------------------ components ---
function StatusBadge({ safe }) {
  if (safe === null || safe === undefined) {
    return <span className="badge badge-na">No data</span>;
  }
  return <span className={`badge ${safe ? 'badge-safe' : 'badge-unsafe'}`}>{safe ? 'Safe' : 'Unsafe'}</span>;
}

function MetricCard({ title, value, unit, safe, footnote }) {
  return (
    <div className={`card ${safe === false ? 'card-unsafe' : ''}`}>
      <div className="card-title">{title}</div>
      <div className="card-value">
        {value}
        <span className="card-unit"> {unit}</span>
      </div>
      <StatusBadge safe={safe} />
      {footnote && <div className="card-foot">{footnote}</div>}
    </div>
  );
}

// Dot on the line is green when the sensor flagged the reading safe, red otherwise
function SafetyDot({ cx, cy, payload }) {
  if (cx == null || cy == null || payload?.value == null) return null;
  return (
    <circle
      cx={cx}
      cy={cy}
      r={5}
      fill={payload.safe ? '#16a34a' : '#dc2626'}
      stroke="#ffffff"
      strokeWidth={1.5}
    />
  );
}

function ChartTooltip({ active, payload, unit, decimals }) {
  if (!active || !payload?.length) return null;
  const p = payload[0].payload;
  return (
    <div className="tooltip">
      <div className="tip-time">{p.label}</div>
      <strong>
        {fmtNum(p.value, decimals)} {unit}
      </strong>
      <div className={p.safe ? 'txt-safe' : 'txt-unsafe'}>{p.safe ? 'Safe' : 'Unsafe'}</div>
      {p.tag && <div className="tip-tag">{p.tag}</div>}
    </div>
  );
}

function TrendChart({ rows, param }) {
  const data = useMemo(
    () =>
      rows.map((r) => ({
        label: fmtTime(r.generated_at),
        value: r[param.key],
        safe: r[param.safeKey],
        tag: r[param.tagKey],
      })),
    [rows, param]
  );

  const { lo, hi, bandLo, bandHi } = useMemo(() => {
    const vals = data.map((d) => d.value).filter((v) => v !== null && v !== undefined);
    const dMin = vals.length ? Math.min(...vals) : 0;
    const dMax = vals.length ? Math.max(...vals) : 1;
    const sMin = param.safe.min ?? -Infinity;
    const sMax = param.safe.max ?? Infinity;

    const lo0 = Math.min(dMin, Number.isFinite(sMin) ? sMin : dMin);
    const hi0 = Math.max(dMax, Number.isFinite(sMax) ? sMax : dMax);
    const pad = (hi0 - lo0) * 0.1 || 1;
    const low = lo0 >= 0 ? Math.max(0, lo0 - pad) : lo0 - pad;
    const high = hi0 + pad;

    return {
      lo: low,
      hi: high,
      bandLo: Number.isFinite(sMin) ? sMin : low,
      bandHi: Number.isFinite(sMax) ? sMax : high,
    };
  }, [data, param]);

  return (
    <div className="chart-wrap">
      <ResponsiveContainer width="100%" height={340}>
        <LineChart data={data} margin={{ top: 12, right: 24, bottom: 8, left: 8 }}>
          <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
          <XAxis dataKey="label" tick={{ fontSize: 12, fill: '#64748b' }} minTickGap={24} />
          <YAxis
            domain={[lo, hi]}
            tick={{ fontSize: 12, fill: '#64748b' }}
            tickFormatter={(v) => Number(v).toFixed(param.decimals > 1 ? 1 : 0)}
            width={64}
            label={{
              value: param.unit,
              angle: -90,
              position: 'insideLeft',
              style: { fill: '#64748b', fontSize: 12 },
            }}
          />
          <ReferenceArea y1={bandLo} y2={bandHi} fill="#16a34a" fillOpacity={0.1} stroke="none" />
          <Tooltip content={<ChartTooltip unit={param.unit} decimals={param.decimals} />} />
          <Line
            type="monotone"
            dataKey="value"
            stroke="#475569"
            strokeWidth={2}
            dot={<SafetyDot />}
            activeDot={<SafetyDot />}
            isAnimationActive={false}
            connectNulls
          />
        </LineChart>
      </ResponsiveContainer>

      <div className="legend">
        <span className="legend-item">
          <i className="dot dot-safe" /> Safe reading
        </span>
        <span className="legend-item">
          <i className="dot dot-unsafe" /> Unsafe reading
        </span>
        <span className="legend-item">
          <i className="band" /> Safe range
        </span>
      </div>
    </div>
  );
}

// ------------------------------------------------------------------- app ---
export default function App() {
  const [windowSize, setWindowSize] = useState(DEFAULT_WINDOW);
  const [activeKey, setActiveKey] = useState(PARAMS[0].key);
  const { rows, error, lastUpdated, loading } = useReadings(windowSize);

  const windowOptions = useMemo(
    () => [...new Set([DEFAULT_WINDOW, ...WINDOW_OPTIONS])].sort((a, b) => a - b),
    []
  );

  const latest = rows.length ? rows[rows.length - 1] : null;
  const activeParam = PARAMS.find((p) => p.key === activeKey) ?? PARAMS[0];

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>Water Quality Dashboard</h1>
          <p className="subtitle">
            Live readings from the monitoring station · refreshes every {REFRESH_MS / 1000}s
          </p>
        </div>

        <div className="header-right">
          <label className="select-label">
            Window size
            <select value={windowSize} onChange={(e) => setWindowSize(Number(e.target.value))}>
              {windowOptions.map((n) => (
                <option key={n} value={n}>
                  Last {n} readings
                </option>
              ))}
            </select>
          </label>

          <div className={`live ${error ? 'live-error' : ''}`}>
            <span className="live-dot" />
            {error
              ? 'Connection problem'
              : lastUpdated
              ? `Updated ${lastUpdated.toLocaleTimeString('en-IN', { hour12: false })}`
              : 'Connecting…'}
          </div>
        </div>
      </header>

      {error && (
        <div className="banner">
          Could not load data: {error}. Showing the last successful data and retrying automatically.
        </div>
      )}

      {loading && !rows.length ? (
        <div className="empty">Loading…</div>
      ) : !rows.length ? (
        <div className="empty">No readings found in the database yet.</div>
      ) : (
        <>
          <section>
            <h2>
              For last {rows.length} {rows.length === 1 ? 'window' : 'windows'}
              <span className="h2-note"> (average of the latest {rows.length} readings)</span>
            </h2>
            <div className="grid">
              {PARAMS.map((p) => {
                const avg = average(rows, p.key);
                return (
                  <MetricCard
                    key={p.key}
                    title={p.avgLabel}
                    value={fmtNum(avg, p.decimals)}
                    unit={p.unit}
                    safe={isSafe(p, avg)}
                  />
                );
              })}
            </div>
          </section>

          <section>
            <h2>
              Current measurements
              {latest && <span className="h2-note"> (as of {fmtTime(latest.generated_at)})</span>}
            </h2>
            <div className="grid">
              {PARAMS.map((p) => (
                <MetricCard
                  key={p.key}
                  title={`Current ${p.label.toLowerCase()}`}
                  value={fmtNum(latest?.[p.key], p.decimals)}
                  unit={p.unit}
                  safe={latest ? latest[p.safeKey] : null}
                  footnote={latest?.[p.tagKey]}
                />
              ))}
            </div>
          </section>

          <section>
            <div className="chart-head">
              <h2>Graphical changes over time</h2>
              <div className="tabs" role="tablist">
                {PARAMS.map((p) => (
                  <button
                    key={p.key}
                    role="tab"
                    aria-selected={p.key === activeKey}
                    className={`tab ${p.key === activeKey ? 'tab-active' : ''}`}
                    onClick={() => setActiveKey(p.key)}
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </div>
            <div className="panel">
              <TrendChart rows={rows} param={activeParam} />
            </div>
          </section>
        </>
      )}
    </div>
  );
}
