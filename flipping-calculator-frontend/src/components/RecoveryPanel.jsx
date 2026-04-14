import {} from 'react';
import { useRecoveryAnalysis } from '../hooks/useApi';
import { formatGP, formatPercent } from '../utils/formatters';

const RECOMMENDATION_CONFIG = {
  SELL: {
    label: 'Sell Now',
    color: 'text-osrs-green',
    bg: 'bg-green-900 bg-opacity-30 border-green-700',
    icon: '✅',
  },
  HOLD: {
    label: 'Hold',
    color: 'text-osrs-green',
    bg: 'bg-green-900 bg-opacity-20 border-green-800',
    icon: '💎',
  },
  HOLD_CAUTIOUS: {
    label: 'Hold (Cautious)',
    color: 'text-yellow-400',
    bg: 'bg-yellow-900 bg-opacity-20 border-yellow-800',
    icon: '⏳',
  },
  UNCERTAIN: {
    label: 'Uncertain',
    color: 'text-yellow-400',
    bg: 'bg-yellow-900 bg-opacity-20 border-yellow-800',
    icon: '⚖️',
  },
  CUT_LOSSES: {
    label: 'Cut Losses',
    color: 'text-osrs-red',
    bg: 'bg-red-900 bg-opacity-20 border-red-800',
    icon: '⚠️',
  },
  CUT_LOSSES_URGENT: {
    label: 'Cut Losses (Urgent)',
    color: 'text-red-400',
    bg: 'bg-red-900 bg-opacity-30 border-red-700',
    icon: '🚨',
  },
};

const TREND_EMOJI = {
  recovering: '📈',
  stabilising: '➡️',
  flat: '➖',
  declining: '📉',
  crashing: '🔻',
};

export default function RecoveryPanel({ flipId }) {
  const { data: analysis, isLoading, error } = useRecoveryAnalysis(flipId);

  if (isLoading) {
    return (
      <div className="border-t border-gray-600 mt-3 pt-3">
        <p className="text-xs text-gray-500">Loading recovery analysis...</p>
      </div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="border-t border-gray-600 mt-3 pt-3">
        <p className="text-xs text-gray-500">Recovery analysis unavailable</p>
      </div>
    );
  }

  const config = RECOMMENDATION_CONFIG[analysis.recommendation] || RECOMMENDATION_CONFIG.UNCERTAIN;
  const trendEmoji = TREND_EMOJI[analysis.trend?.direction] || '➖';
  const underwater = analysis.distance_pct < 0;

  return (
    <div className="border-t border-gray-600 mt-3 pt-3">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-xs text-gray-400 uppercase tracking-wide">Recovery Analysis</span>
      </div>

      {/* Recommendation banner */}
      <div className={`rounded-lg border p-3 mb-3 ${config.bg}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-lg">{config.icon}</span>
            <span className={`font-bold ${config.color}`}>{config.label}</span>
          </div>
          <div className="text-right">
            <span className="text-sm text-gray-400">Recovery chance</span>
            <p className={`text-lg font-bold ${
              analysis.recovery_probability >= 60 ? 'text-osrs-green' :
              analysis.recovery_probability >= 40 ? 'text-yellow-400' : 'text-osrs-red'
            }`}>
              {analysis.recovery_probability}%
            </p>
          </div>
        </div>
        <p className="text-xs text-gray-400 mt-2">{analysis.reasoning}</p>
      </div>

      {/* Metrics grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 md:gap-3 text-sm">
        <div>
          <p className="text-xs text-gray-500 mb-1">Distance</p>
          <p className={`font-bold ${underwater ? 'text-osrs-red' : 'text-osrs-green'}`}>
            {analysis.distance_pct > 0 ? '+' : ''}{formatPercent(analysis.distance_pct)}
          </p>
          <p className="text-xs text-gray-500">
            {underwater ? '' : '+'}{formatGP(analysis.distance_gp)}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500 mb-1">Trend (24h)</p>
          <p className="font-medium">
            {trendEmoji} <span className="capitalize">{analysis.trend?.direction}</span>
          </p>
          <p className="text-xs text-gray-500">
            {analysis.trend?.recent_24h_pct > 0 ? '+' : ''}{analysis.trend?.recent_24h_pct}%/6h
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500 mb-1">Volatility</p>
          <p className="font-medium">
            {analysis.volatility?.pct_per_6h > 3 ? '🔥' :
             analysis.volatility?.pct_per_6h > 1 ? '📊' : '😴'}{' '}
            {analysis.volatility?.pct_per_6h}%/6h
          </p>
          <p className="text-xs text-gray-500">
            Range: {formatPercent(analysis.volatility?.price_range_pct)}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500 mb-1">History</p>
          <p className="font-medium">
            {analysis.historical?.above_buy_rate}% above buy
          </p>
          {analysis.historical?.dip_recovery_rate != null && (
            <p className="text-xs text-gray-500">
              Dip recovery: {analysis.historical.dip_recovery_rate}%
            </p>
          )}
        </div>
      </div>
    </div>
  );
}