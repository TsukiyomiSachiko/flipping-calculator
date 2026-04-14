import { useState, useEffect } from 'react';
import { useTrajectory } from '../hooks/useApi';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { formatGP } from '../utils/formatters';

/**
 * Market Trajectory Chart
 *
 * Thin display component — all computation happens in the API.
 * Renders smoothed price history + forward projection with confidence bands.
 * Has its own timestep selector independent of the price history chart.
 * Auto-detects the best timestep by trying 5m → 1h → 6h and defaulting
 * to the first one that returns enough data.
 */

const TIMESTEPS = [
  { key: '5m', label: '5 Min' },
  { key: '1h', label: '1 Hour' },
  { key: '6h', label: '6 Hour' },
];

function TrajectoryTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  const point = payload[0]?.payload;
  if (!point) return null;

  return (
    <div className="bg-gray-900 border border-gray-600 rounded p-2 text-xs">
      <p className="text-gray-400 mb-1">{new Date(label * 1000).toLocaleString()}</p>
      {point.isProjection ? (
        <>
          <p className="text-orange-400">Projected: {formatGP(point.trendLine)}</p>
          {point.upper != null && (
            <p className="text-gray-500">
              Range: {formatGP(point.lower)} – {formatGP(point.upper)}
            </p>
          )}
        </>
      ) : (
        <>
          {point.buyPrice && <p className="text-red-400">Buy: {formatGP(point.buyPrice)}</p>}
          {point.sellPrice && <p className="text-green-400">Sell: {formatGP(point.sellPrice)}</p>}
          {point.smoothed && <p className="text-orange-400">Trend: {formatGP(point.smoothed)}</p>}
        </>
      )}
    </div>
  );
}

// Inner component that renders once we have a selected timestep
function TrajectoryChart({ itemId, timestep, compact, onAvailable, onUnavailable }) {
  const { data, isLoading, error } = useTrajectory(itemId, timestep);

  useEffect(() => {
    if (data && !error) {
      onAvailable?.(timestep);
    } else if (!isLoading && (error || !data)) {
      onUnavailable?.(timestep);
    }
  }, [data, error, isLoading, timestep, onAvailable, onUnavailable]);

  if (isLoading) {
    return (
      <div className="p-4">
        <p className="text-gray-400 text-sm text-center">Loading trajectory...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-4">
        <p className="text-gray-500 text-sm text-center">
          {error?.response?.status === 422
            ? 'Not enough data at this interval'
            : error ? 'Failed to load trajectory' : 'No trajectory data'}
        </p>
      </div>
    );
  }

  const { history, projection, trend, stats, lastHistoricalTimestamp } = data;

  const chartData = [
    ...history.map(p => ({ ...p, isProjection: false })),
    ...projection.map(p => ({ ...p, isProjection: true })),
  ];

  const chartHeight = compact ? 200 : 280;

  return (
    <>
      {/* Trend badge + projected change */}
      <div className="flex items-center justify-between px-3 md:px-4 py-2">
        <div className="flex items-center gap-2">
          <span className="text-sm">{trend.emoji}</span>
          <span
            className="text-xs font-bold px-2 py-0.5 rounded capitalize"
            style={{ color: trend.color, backgroundColor: `${trend.color}20` }}
          >
            {trend.direction.replace('_', ' ')}
          </span>
        </div>
        <div className="text-right">
          <span
            className="text-sm font-bold"
            style={{ color: stats.projectedChange >= 0 ? '#10B981' : '#EF4444' }}
          >
            {stats.projectedChange >= 0 ? '+' : ''}{formatGP(stats.projectedChange)}
          </span>
          <span className="text-xs text-gray-500 ml-1">
            ({stats.projectedChangePct}%) in {stats.projectionWindow}
          </span>
        </div>
      </div>

      {/* Chart */}
      <div className="p-2 md:p-4 pt-0 md:pt-0">
        <ResponsiveContainer width="100%" height={chartHeight}>
          <LineChart data={chartData} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
            <XAxis
              dataKey="timestamp"
              stroke="#4B5563"
              tick={{ fontSize: 10 }}
              tickFormatter={(ts) => {
                const d = new Date(ts * 1000);
                if (timestep === '5m') return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                if (timestep === '1h') return d.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit' });
                return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
              }}
            />
            <YAxis
              stroke="#4B5563"
              tick={{ fontSize: 10 }}
              tickFormatter={(v) => formatGP(v)}
              domain={['auto', 'auto']}
            />
            <Tooltip content={<TrajectoryTooltip />} />

            <ReferenceLine
              x={lastHistoricalTimestamp}
              stroke="#6B7280"
              strokeDasharray="4 4"
              strokeWidth={1}
            />

            <Line type="monotone" dataKey="upper" stroke={trend.color} strokeWidth={1} strokeOpacity={0.25} strokeDasharray="3 3" dot={false} connectNulls={false} isAnimationActive={false} />
            <Line type="monotone" dataKey="lower" stroke={trend.color} strokeWidth={1} strokeOpacity={0.25} strokeDasharray="3 3" dot={false} connectNulls={false} isAnimationActive={false} />

            {!compact && (
              <>
                <Line type="monotone" dataKey="buyPrice" stroke="#EF4444" strokeWidth={1} strokeOpacity={0.3} dot={false} connectNulls={false} isAnimationActive={false} />
                <Line type="monotone" dataKey="sellPrice" stroke="#10B981" strokeWidth={1} strokeOpacity={0.3} dot={false} connectNulls={false} isAnimationActive={false} />
              </>
            )}

            <Line type="monotone" dataKey="smoothed" stroke={trend.color} strokeWidth={2} dot={false} connectNulls={false} isAnimationActive={false} />
            <Line type="monotone" dataKey="trendLine" stroke={trend.color} strokeWidth={2} strokeDasharray="6 3" dot={false} connectNulls={false} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-2 p-3 md:p-4 border-t border-gray-700 text-center">
        <div>
          <p className="text-xs text-gray-500">Current</p>
          <p className="text-sm font-bold text-gray-300">{formatGP(stats.currentSmoothed)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Projected</p>
          <p className="text-sm font-bold" style={{ color: trend.color }}>
            {formatGP(stats.projectedEnd)}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Volatility</p>
          <p className="text-sm font-bold text-gray-300">±{formatGP(stats.volatility)}</p>
        </div>
      </div>
    </>
  );
}

export default function MarketTrajectory({ itemId, compact = false }) {
  const [selectedTimestep, setSelectedTimestep] = useState(null);
  const [autoDetecting, setAutoDetecting] = useState(true);
  const [, setAvailableTimesteps] = useState(new Set());
  const [unavailableTimesteps, setUnavailableTimesteps] = useState(new Set());

  // Auto-detection: try 5m first, then 1h, then 6h
  const detectOrder = ['5m', '1h', '6h'];
  const detectTimestep = autoDetecting ? detectOrder.find(
    ts => !unavailableTimesteps.has(ts)
  ) : null;

  const handleAvailable = (ts) => {
    setAvailableTimesteps(prev => new Set(prev).add(ts));
    if (autoDetecting) {
      setSelectedTimestep(ts);
      setAutoDetecting(false);
    }
  };

  const handleUnavailable = (ts) => {
    setUnavailableTimesteps(prev => {
      const next = new Set(prev).add(ts);
      // If all timesteps failed, stop detecting
      if (detectOrder.every(t => next.has(t))) {
        setAutoDetecting(false);
      }
      return next;
    });
  };

  // Once a user manually picks a timestep, mark the available ones
  const activeTimestep = autoDetecting ? detectTimestep : selectedTimestep;

  // If all failed during auto-detect
  if (!autoDetecting && !selectedTimestep) {
    return (
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
        <p className="text-gray-500 text-sm text-center">Not enough price data for trajectory analysis</p>
      </div>
    );
  }

  // Still auto-detecting and ran out of options
  if (autoDetecting && !detectTimestep) {
    return (
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
        <p className="text-gray-500 text-sm text-center">Not enough price data for trajectory analysis</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700">
      {/* Header with timestep selector */}
      <div className="flex items-center justify-between p-3 md:p-4 border-b border-gray-700">
        <span className="text-sm font-semibold text-gray-300">Market Trajectory</span>
        {!autoDetecting && (
          <div className="flex gap-1">
            {TIMESTEPS.map(({ key, label }) => (
              <button
                key={key}
                className={`px-2 py-1 rounded text-xs transition-colors ${
                  activeTimestep === key
                    ? 'bg-osrs-gold text-black font-bold'
                    : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
                }`}
                onClick={() => {
                  setSelectedTimestep(key);
                }}
              >
                {label}
              </button>
            ))}
          </div>
        )}
      </div>

      {activeTimestep && (
        <TrajectoryChart
          key={activeTimestep}
          itemId={itemId}
          timestep={activeTimestep}
          compact={compact}
          onAvailable={handleAvailable}
          onUnavailable={handleUnavailable}
        />
      )}
    </div>
  );
}