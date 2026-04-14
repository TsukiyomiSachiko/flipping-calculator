import { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';
import { useMargins } from '../hooks/useApi';

export default function MarginChart({ itemId, itemName }) {
  const [period, setPeriod] = useState('168'); // 7 days
  const [interval, setInterval] = useState('1h');

  const { data, isLoading, error } = useMargins(itemId, period, interval);

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp * 1000);
    if (interval === '1h') {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) + ' ' + 
             date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    } else if (interval === '6h') {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) + ' ' + 
             date.toLocaleTimeString('en-US', { hour: '2-digit' });
    } else {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
  };

  const getTrendIcon = (direction) => {
    if (direction === 'increasing') return '📈';
    if (direction === 'decreasing') return '📉';
    return '➡️';
  };

  const getTrendColor = (direction) => {
    if (direction === 'increasing') return 'text-green-400';
    if (direction === 'decreasing') return 'text-red-400';
    return 'text-gray-400';
  };

  if (isLoading && !data) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-400">Loading margin analysis...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gray-800 rounded-lg p-4 md:p-6 space-y-4 md:space-y-6">
        {/* Header with Controls - Always visible */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h3 className="text-lg md:text-xl font-bold text-white">📊 Margin Analysis</h3>
            <p className="text-gray-400 text-sm">{itemName}</p>
          </div>

          {/* Controls - Keep visible so user can change timestep */}
          <div className="flex gap-2 md:gap-4">
            {/* Period selector */}
            <select
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              className="bg-gray-700 text-white px-2 md:px-3 py-2 rounded text-sm"
            >
              <option value="24">24 Hours</option>
              <option value="168">7 Days</option>
              <option value="336">14 Days</option>
              <option value="720">30 Days</option>
            </select>

            {/* Interval selector */}
            <select
              value={interval}
              onChange={(e) => setInterval(e.target.value)}
              className="bg-gray-700 text-white px-2 md:px-3 py-2 rounded text-sm"
            >
              <option value="1h">Hourly</option>
              <option value="6h">6 Hour</option>
              <option value="1d">Daily</option>
            </select>
          </div>
        </div>

        {/* Error message */}
        <div className="flex flex-col items-center justify-center h-48 md:h-64">
          <div className="text-red-400 mb-2">{error}</div>
          <div className="text-gray-500 text-sm text-center max-w-md">
            {error.includes('Insufficient') 
              ? 'Try a longer time period or different interval. Background polling will collect more data over time.'
              : 'Try again later or contact support.'}
          </div>
        </div>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  // Prepare chart data (reverse to show chronologically)
  const chartData = [...data.data].reverse().map(point => ({
    ...point,
    time: formatTimestamp(point.timestamp)
  }));

  return (
    <div className="bg-gray-800 rounded-lg p-4 md:p-6 space-y-4 md:space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h3 className="text-lg md:text-xl font-bold text-white">📊 Margin Analysis</h3>
          <p className="text-gray-400 text-sm">{itemName}</p>
        </div>

        {/* Controls */}
        <div className="flex gap-2 md:gap-4">
          {/* Period selector */}
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="bg-gray-700 text-white px-2 md:px-3 py-2 rounded text-sm"
          >
            <option value="24">24 Hours</option>
            <option value="168">7 Days</option>
            <option value="336">14 Days</option>
            <option value="720">30 Days</option>
          </select>

          {/* Interval selector */}
          <select
            value={interval}
            onChange={(e) => setInterval(e.target.value)}
            className="bg-gray-700 text-white px-2 md:px-3 py-2 rounded text-sm"
          >
            <option value="1h">1 Hour</option>
            <option value="6h">6 Hours</option>
            <option value="1d">1 Day</option>
          </select>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
        <div className="bg-gray-700 rounded p-3 md:p-4">
          <div className="text-gray-400 text-xs uppercase">Current Margin</div>
          <div className="text-xl md:text-2xl font-bold text-white">{data.current_margin}%</div>
        </div>
        <div className="bg-gray-700 rounded p-3 md:p-4">
          <div className="text-gray-400 text-xs uppercase">Average Margin</div>
          <div className="text-xl md:text-2xl font-bold text-white">{data.avg_margin}%</div>
        </div>
        <div className="bg-gray-700 rounded p-3 md:p-4">
          <div className="text-gray-400 text-xs uppercase">Max Margin</div>
          <div className="text-xl md:text-2xl font-bold text-green-400">{data.max_margin}%</div>
        </div>
        <div className="bg-gray-700 rounded p-3 md:p-4">
          <div className="text-gray-400 text-xs uppercase">Min Margin</div>
          <div className="text-xl md:text-2xl font-bold text-red-400">{data.min_margin}%</div>
        </div>
      </div>

      {/* Trend Indicator */}
      <div className="bg-gray-700 rounded p-4 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        <div>
          <div className="text-gray-400 text-sm">Trend</div>
          <div className={`text-base md:text-lg font-bold ${getTrendColor(data.trend.direction)}`}>
            {getTrendIcon(data.trend.direction)} {data.trend.direction.charAt(0).toUpperCase() + data.trend.direction.slice(1)}
            {data.trend.strength > 0 && ` (${data.trend.strength.toFixed(1)}% strength)`}
          </div>
        </div>
        <div className="md:text-right">
          <div className="text-gray-400 text-sm">Interpretation</div>
          <div className="text-white text-sm">
            {data.trend.direction === 'increasing' && 'Margins are improving - good time to flip'}
            {data.trend.direction === 'decreasing' && 'Margins are declining - consider waiting'}
            {data.trend.direction === 'stable' && 'Margins are stable - consistent opportunity'}
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="bg-gray-900 rounded p-2 md:p-4">
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis 
              dataKey="time" 
              stroke="#9CA3AF"
              tick={{ fontSize: 10 }}
              angle={-45}
              textAnchor="end"
              height={70}
            />
            <YAxis 
              stroke="#9CA3AF"
              tick={{ fontSize: 11 }}
              label={{ value: 'Margin %', angle: -90, position: 'insideLeft', style: { fill: '#9CA3AF', fontSize: 12 } }}
            />
            <Tooltip 
              contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', fontSize: '12px' }}
              labelStyle={{ color: '#9CA3AF' }}
              formatter={(value, name) => {
                if (name === 'margin_percent') return [`${value}%`, 'Margin'];
                return [value, name];
              }}
            />
            <Legend wrapperStyle={{ fontSize: '12px' }} />
            <ReferenceLine y={data.avg_margin} stroke="#6B7280" strokeDasharray="5 5" label={{ value: 'Avg', fontSize: 11, fill: '#9CA3AF' }} />
            <Line 
              type="monotone" 
              dataKey="margin_percent" 
              stroke="#10B981" 
              strokeWidth={2}
              dot={{ fill: '#10B981', r: 2 }}
              activeDot={{ r: 4 }}
              name="Margin %"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Peak Times */}
      {data.peak_times && data.peak_times.length > 0 && (
        <div className="bg-gray-700 rounded p-4">
          <h4 className="text-white font-bold mb-3 text-sm md:text-base">🕐 Best Trading Times</h4>
          <div className="space-y-2">
            {data.peak_times.slice(0, 3).map((peak, idx) => (
              <div key={idx} className="flex justify-between items-center text-sm">
                <div className="text-white">
                  {String(peak.hour).padStart(2, '0')}:00 ({peak.day_type})
                </div>
                <div className="flex items-center gap-2">
                  <div className="text-green-400 font-bold">{peak.avg_margin}%</div>
                  <div className="text-gray-400 text-xs hidden md:inline">({peak.sample_count} samples)</div>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-3 text-xs md:text-sm text-gray-400">
            💡 Margins tend to be higher during these times. Consider timing your flips accordingly!
          </div>
        </div>
      )}
    </div>
  );
}