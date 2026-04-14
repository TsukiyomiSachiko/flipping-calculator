import { useState } from 'react';
import { usePriceHistory } from '../hooks/useApi';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { formatGP } from '../utils/formatters';
import MarketTrajectory from './MarketTrajectory';

export default function PriceHistoryModal({ isOpen, itemId, itemName, onClose }) {
  const [timestep, setTimestep] = useState('5m');
  const { data, isLoading, error } = usePriceHistory(itemId, timestep);

  if (!isOpen) return null;

  // Format data for recharts and filter outliers
  const rawChartData = data?.data?.map(point => ({
    timestamp: point.timestamp,
    date: new Date(point.timestamp * 1000).toLocaleString(),
    buyPrice: point.avgHighPrice,
    sellPrice: point.avgLowPrice,
    spread: point.avgHighPrice - point.avgLowPrice,
  })) || [];

  // Filter out null/undefined values and calculate statistics
  const validData = rawChartData.filter(point => 
    point.buyPrice != null && 
    point.sellPrice != null && 
    point.buyPrice > 0 && 
    point.sellPrice > 0
  );

  // Calculate median and IQR for outlier detection
  const allPrices = validData.flatMap(point => [point.buyPrice, point.sellPrice]);
  allPrices.sort((a, b) => a - b);
  
  const median = allPrices[Math.floor(allPrices.length / 2)] || 0;
  const q1 = allPrices[Math.floor(allPrices.length * 0.25)] || 0;
  const q3 = allPrices[Math.floor(allPrices.length * 0.75)] || 0;
  const iqr = q3 - q1;
  
  // Remove extreme outliers (beyond 3x IQR from median)
  const lowerBound = Math.max(0, median - (iqr * 3));
  const upperBound = median + (iqr * 3);
  
  const chartData = validData.filter(point => {
    const avgPrice = (point.buyPrice + point.sellPrice) / 2;
    return avgPrice >= lowerBound && avgPrice <= upperBound;
  });

  // Calculate Y-axis domain with 10% padding
  const minPrice = Math.min(...chartData.flatMap(p => [p.buyPrice, p.sellPrice]));
  const maxPrice = Math.max(...chartData.flatMap(p => [p.buyPrice, p.sellPrice]));
  const padding = (maxPrice - minPrice) * 0.1;
  const yAxisDomain = [
    Math.max(0, Math.floor(minPrice - padding)),
    Math.ceil(maxPrice + padding)
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-[70] p-2 md:p-4">
      <div className="bg-gray-800 rounded-lg w-full max-w-6xl max-h-[90vh] overflow-auto border border-gray-700">
        {/* Header */}
        <div className="sticky top-0 bg-gray-800 border-b border-gray-700 p-4 md:p-6 flex justify-between items-center">
          <div>
            <h2 className="text-lg md:text-2xl font-bold text-white">{itemName}</h2>
            <p className="text-sm text-gray-400">Price History</p>
          </div>
          <button
            className="text-gray-400 hover:text-white text-2xl"
            onClick={onClose}
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="p-3 md:p-6">
          {/* Timestep selector */}
          <div className="flex gap-1 md:gap-2 mb-4 md:mb-6">
            <button
              className={`flex-1 md:flex-none px-3 md:px-4 py-2 rounded text-sm transition-colors ${
                timestep === '5m'
                  ? 'bg-osrs-gold text-black'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
              onClick={() => setTimestep('5m')}
            >
              5 Min
            </button>
            <button
              className={`flex-1 md:flex-none px-3 md:px-4 py-2 rounded text-sm transition-colors ${
                timestep === '1h'
                  ? 'bg-osrs-gold text-black'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
              onClick={() => setTimestep('1h')}
            >
              1 Hour
            </button>
            <button
              className={`flex-1 md:flex-none px-3 md:px-4 py-2 rounded text-sm transition-colors ${
                timestep === '6h'
                  ? 'bg-osrs-gold text-black'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
              onClick={() => setTimestep('6h')}
            >
              6 Hour
            </button>
          </div>

          {/* Loading state */}
          {isLoading && (
            <div className="text-center py-12">
              <p className="text-gray-400">Loading price history...</p>
            </div>
          )}

          {/* Error state */}
          {error && (
            <div className="text-center py-12">
              <p className="text-red-400">Error loading price history: {error.message}</p>
            </div>
          )}

          {/* Chart */}
          {!isLoading && !error && chartData.length > 0 && (
            <div className="bg-gray-900 rounded-lg p-4">
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis 
                    dataKey="timestamp" 
                    stroke="#9CA3AF"
                    tickFormatter={(timestamp) => {
                      const date = new Date(timestamp * 1000);
                      if (timestep === '5m') {
                        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                      } else if (timestep === '1h') {
                        return date.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit' });
                      } else {
                        return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
                      }
                    }}
                  />
                  <YAxis 
                    stroke="#9CA3AF"
                    tickFormatter={(value) => formatGP(value)}
                    domain={yAxisDomain}
                  />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }}
                    labelStyle={{ color: '#D1D5DB' }}
                    formatter={(value) => formatGP(value)}
                    labelFormatter={(timestamp) => new Date(timestamp * 1000).toLocaleString()}
                  />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="buyPrice" 
                    stroke="#EF4444" 
                    name="Buy Price (High)"
                    strokeWidth={2}
                    dot={false}
                    connectNulls={true}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="sellPrice" 
                    stroke="#10B981" 
                    name="Sell Price (Low)"
                    strokeWidth={2}
                    dot={false}
                    connectNulls={true}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* No data */}
          {!isLoading && !error && chartData.length === 0 && (
            <div className="text-center py-12">
              <p className="text-gray-400">No price history data available for this item.</p>
            </div>
          )}

          {/* Market Trajectory */}
          {!isLoading && !error && chartData.length > 0 && (
            <div className="mt-4 md:mt-6">
              <MarketTrajectory itemId={itemId} itemName={itemName} />
            </div>
          )}

          {/* Summary stats */}
          {!isLoading && !error && chartData.length > 0 && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
              <div className="bg-gray-700 rounded p-4">
                <p className="text-xs text-gray-400 mb-1">Current Buy</p>
                <p className="text-lg font-bold text-osrs-red">
                  {formatGP(chartData[chartData.length - 1]?.buyPrice)}
                </p>
              </div>
              <div className="bg-gray-700 rounded p-4">
                <p className="text-xs text-gray-400 mb-1">Current Sell</p>
                <p className="text-lg font-bold text-osrs-green">
                  {formatGP(chartData[chartData.length - 1]?.sellPrice)}
                </p>
              </div>
              <div className="bg-gray-700 rounded p-4">
                <p className="text-xs text-gray-400 mb-1">Current Spread</p>
                <p className="text-lg font-bold text-osrs-gold">
                  {formatGP(chartData[chartData.length - 1]?.spread)}
                </p>
              </div>
              <div className="bg-gray-700 rounded p-4">
                <p className="text-xs text-gray-400 mb-1">Data Points</p>
                <p className="text-lg font-bold text-gray-300">
                  {chartData.length}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}