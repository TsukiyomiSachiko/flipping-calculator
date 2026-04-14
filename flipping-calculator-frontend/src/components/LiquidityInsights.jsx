import {} from 'react';
import { useLiquidityInsights } from '../hooks/useApi';

export default function LiquidityInsights({ itemId }) {
  const { data: insights, isLoading, error } = useLiquidityInsights(itemId);

  if (isLoading) {
    return (
      <div className="bg-gray-700 rounded-lg p-4">
        <h3 className="text-lg font-bold mb-2 text-osrs-gold">📊 Liquidity Timing</h3>
        <p className="text-gray-400 text-sm">Loading liquidity analysis...</p>
      </div>
    );
  }

  if (error || !insights) {
    return null; // Don't show if there's an error or no data
  }

  // Don't show if insufficient data
  if (insights.pattern === 'insufficient_data' || insights.pattern === 'no_data') {
    return (
      <div className="bg-gray-700 rounded-lg p-4">
        <h3 className="text-lg font-bold mb-2 text-osrs-gold">📊 Liquidity Timing</h3>
        <p className="text-gray-400 text-sm">{insights.message || 'Not enough data to analyze fill patterns'}</p>
      </div>
    );
  }

  // Pattern emoji and color
  const patternConfig = {
    consistent: { emoji: '✅', color: 'text-green-400', label: 'Consistent' },
    moderate: { emoji: '🟡', color: 'text-yellow-400', label: 'Moderate' },
    intermittent: { emoji: '⚠️', color: 'text-yellow-600', label: 'Intermittent' },
    sparse: { emoji: '🔴', color: 'text-red-400', label: 'Sparse' },
  };

  const config = patternConfig[insights.pattern] || { emoji: '❓', color: 'text-gray-400', label: 'Unknown' };

  return (
    <div className="bg-gray-700 rounded-lg p-4">
      <h3 className="text-lg font-bold mb-3 text-osrs-gold">📊 Liquidity Timing</h3>

      {/* Pattern indicator */}
      <div className="mb-4 p-3 bg-gray-800 rounded-lg">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-2xl">{config.emoji}</span>
          <div>
            <p className={`font-bold ${config.color}`}>{config.label} Fill Pattern</p>
            <p className="text-sm text-gray-400">{insights.pattern_description}</p>
          </div>
        </div>

        {/* Estimated fill time */}
        {insights.avg_fill_time_minutes && (
          <div className="mt-2 pt-2 border-t border-gray-700">
            <p className="text-xs text-gray-400">
              Average time between volume spikes: <span className="text-white font-medium">{Math.round(insights.avg_fill_time_minutes)} minutes</span>
            </p>
          </div>
        )}
      </div>

      {/* Best trading hours */}
      {insights.best_hours && insights.best_hours.length > 0 && (
        <div className="mb-4">
          <p className="text-sm font-medium mb-2 text-gray-300">🕐 Best Trading Hours (GMT)</p>
          <div className="grid grid-cols-5 gap-2">
            {insights.best_hours.slice(0, 5).map((hour, idx) => (
              <div
                key={idx}
                className="bg-gray-800 rounded p-2 text-center"
                title={`Avg volume: ${hour.avg_volume.toLocaleString()}`}
              >
                <p className="text-xs font-bold text-osrs-gold">{hour.hour_label}</p>
                <p className="text-xs text-gray-400">#{idx + 1}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Weekend vs Weekday */}
      {insights.weekend_multiplier && (
        <div className="text-xs text-gray-400">
          <p>
            {insights.weekend_multiplier > 1.2 ? (
              <span className="text-green-400">
                ✨ {Math.round((insights.weekend_multiplier - 1) * 100)}% more volume on weekends
              </span>
            ) : insights.weekend_multiplier < 0.8 ? (
              <span className="text-blue-400">
                📈 {Math.round((1 - insights.weekend_multiplier) * 100)}% more volume on weekdays
              </span>
            ) : (
              <span>Similar volume weekdays vs weekends</span>
            )}
          </p>
        </div>
      )}

      {/* Data points info */}
      <p className="text-xs text-gray-500 mt-3">
        Analysis based on {insights.total_data_points} data points over the last 7 days
      </p>
    </div>
  );
}
