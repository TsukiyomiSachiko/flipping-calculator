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
    <div className="fixed inset-0 bg-luxury-darker/80 backdrop-blur-md flex items-center justify-center z-[70] p-2 md:p-4 animate-fade-in">
      <div className="bg-luxury-card backdrop-blur-xl rounded-2xl w-full max-w-6xl max-h-[90vh] overflow-auto border border-luxury-purple/20 shadow-luxury-shadow shadow-purple-glow">
        {/* Header */}
        <div className="sticky top-0 bg-luxury-card/95 backdrop-blur-md border-b border-luxury-border p-4 md:p-6 flex justify-between items-center z-10">
          <div>
            <h2 className="text-lg md:text-2xl font-bold bg-gold-gradient bg-clip-text text-transparent font-cinzel">{itemName}</h2>
            <p className="text-xs text-luxury-purpleLight uppercase tracking-wider font-semibold">Price History</p>
          </div>
          <button
            className="text-luxury-purpleLight hover:text-luxury-gold text-2xl transition-colors duration-200"
            onClick={onClose}
            aria-label="Close modal"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="p-4 md:p-6">
          {/* Timestep selector */}
          <div className="flex gap-2 mb-4 md:mb-6">
            <button
              className={`flex-1 md:flex-none px-5 py-2.5 rounded-xl text-sm font-semibold tracking-wide transition-all duration-300 transform outline-none select-none ${
                timestep === '5m'
                  ? 'bg-gold-gradient text-luxury-darker font-bold shadow-gold-glow scale-[1.02]'
                  : 'bg-luxury-darker/60 text-luxury-purpleLight hover:text-white border border-luxury-purple/20 hover:bg-luxury-purple/10 hover:border-luxury-purple/40'
              }`}
              onClick={() => setTimestep('5m')}
            >
              5 Min
            </button>
            <button
              className={`flex-1 md:flex-none px-5 py-2.5 rounded-xl text-sm font-semibold tracking-wide transition-all duration-300 transform outline-none select-none ${
                timestep === '1h'
                  ? 'bg-gold-gradient text-luxury-darker font-bold shadow-gold-glow scale-[1.02]'
                  : 'bg-luxury-darker/60 text-luxury-purpleLight hover:text-white border border-luxury-purple/20 hover:bg-luxury-purple/10 hover:border-luxury-purple/40'
              }`}
              onClick={() => setTimestep('1h')}
            >
              1 Hour
            </button>
            <button
              className={`flex-1 md:flex-none px-5 py-2.5 rounded-xl text-sm font-semibold tracking-wide transition-all duration-300 transform outline-none select-none ${
                timestep === '6h'
                  ? 'bg-gold-gradient text-luxury-darker font-bold shadow-gold-glow scale-[1.02]'
                  : 'bg-luxury-darker/60 text-luxury-purpleLight hover:text-white border border-luxury-purple/20 hover:bg-luxury-purple/10 hover:border-luxury-purple/40'
              }`}
              onClick={() => setTimestep('6h')}
            >
              6 Hour
            </button>
          </div>

          {/* Loading state */}
          {isLoading && (
            <div className="text-center py-16 text-luxury-purpleLight animate-pulse flex flex-col items-center justify-center gap-3">
              <span className="w-8 h-8 rounded-full border-4 border-t-luxury-gold border-r-luxury-gold border-b-luxury-purple border-l-luxury-purple animate-spin"></span>
              Loading price history...
            </div>
          )}

          {/* Error state */}
          {error && (
            <div className="text-center py-16">
              <p className="text-osrs-red">Error loading price history: {error.message}</p>
            </div>
          )}

          {/* Chart */}
          {!isLoading && !error && chartData.length > 0 && (
            <div className="bg-luxury-darker/40 backdrop-blur-md rounded-xl p-4 border border-luxury-purple/10">
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(139, 92, 246, 0.08)" />
                  <XAxis 
                    dataKey="timestamp" 
                    stroke="rgba(139, 92, 246, 0.5)"
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
                    style={{ fontSize: '11px', fontFamily: 'Outfit, sans-serif' }}
                  />
                  <YAxis 
                    stroke="rgba(139, 92, 246, 0.5)"
                    tickFormatter={(value) => formatGP(value)}
                    domain={yAxisDomain}
                    style={{ fontSize: '11px', fontFamily: 'Outfit, sans-serif' }}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#0c0818', 
                      borderColor: 'rgba(139, 92, 246, 0.25)', 
                      borderRadius: '12px', 
                      boxShadow: '0 10px 30px rgba(0,0,0,0.6)',
                      fontFamily: 'Outfit, sans-serif'
                    }}
                    labelStyle={{ color: '#c084fc', fontWeight: 'bold' }}
                    formatter={(value) => formatGP(value)}
                    labelFormatter={(timestamp) => new Date(timestamp * 1000).toLocaleString()}
                  />
                  <Legend wrapperStyle={{ fontFamily: 'Outfit, sans-serif', fontSize: '12px', marginTop: '10px' }} />
                  <Line 
                    type="monotone" 
                    dataKey="buyPrice" 
                    stroke="#f43f5e" 
                    name="Buy Price (High)"
                    strokeWidth={2}
                    dot={false}
                    connectNulls={true}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="sellPrice" 
                    stroke="#10b981" 
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
            <div className="text-center py-16">
              <p className="text-gray-400 italic">No price history data available for this item.</p>
            </div>
          )}

          {/* Market Trajectory */}
          {!isLoading && !error && chartData.length > 0 && (
            <div className="mt-6">
              <MarketTrajectory itemId={itemId} itemName={itemName} />
            </div>
          )}

          {/* Summary stats */}
          {!isLoading && !error && chartData.length > 0 && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
              <div className="bg-luxury-darker/40 backdrop-blur-md rounded-xl p-4 border border-luxury-purple/10 hover:border-luxury-purple/20 transition-all duration-300">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-luxury-purpleLight/70 mb-1">Current Buy</p>
                <p className="text-lg font-bold font-mono text-osrs-red">
                  {formatGP(chartData[chartData.length - 1]?.buyPrice)}
                </p>
              </div>
              <div className="bg-luxury-darker/40 backdrop-blur-md rounded-xl p-4 border border-luxury-purple/10 hover:border-luxury-purple/20 transition-all duration-300">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-luxury-purpleLight/70 mb-1">Current Sell</p>
                <p className="text-lg font-bold font-mono text-osrs-green">
                  {formatGP(chartData[chartData.length - 1]?.sellPrice)}
                </p>
              </div>
              <div className="bg-luxury-darker/40 backdrop-blur-md rounded-xl p-4 border border-luxury-purple/10 hover:border-luxury-purple/20 transition-all duration-300">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-luxury-purpleLight/70 mb-1">Current Spread</p>
                <p className="text-lg font-bold font-mono text-luxury-gold">
                  {formatGP(chartData[chartData.length - 1]?.spread)}
                </p>
              </div>
              <div className="bg-luxury-darker/40 backdrop-blur-md rounded-xl p-4 border border-luxury-purple/10 hover:border-luxury-purple/20 transition-all duration-300">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-luxury-purpleLight/70 mb-1">Data Points</p>
                <p className="text-lg font-bold font-mono text-white">
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