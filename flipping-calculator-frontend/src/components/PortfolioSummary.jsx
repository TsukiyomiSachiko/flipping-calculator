import {} from 'react';
import { usePortfolioSummary } from '../hooks/useApi';
import { formatGP, formatPercent } from '../utils/formatters';

export default function PortfolioSummary({ projectedProfit, currentValue }) {
  const { data, isLoading, error } = usePortfolioSummary();

  if (isLoading) {
    return (
      <div className="card">
        <p className="text-gray-400">Loading portfolio...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <p className="text-red-400">Error loading portfolio: {error.message}</p>
      </div>
    );
  }

  const stats = data || {};
  
  // Calculate derived values
  const totalInvestment = (stats.total_invested || 0) + (stats.pending_capital || 0);
  const totalReturned = (stats.total_invested || 0) + (stats.total_profit || 0);
  const netProfit = stats.total_profit_all || 0; // Includes profit from partial sells
  const hasProjection = projectedProfit != null && projectedProfit !== 0;

  return (
    <div className="grid grid-cols-2 lg:grid-cols-3 gap-3 md:gap-4 mb-4 md:mb-6">
      <div className="card">
        <h3 className="text-sm text-gray-400 mb-2">Total Investment</h3>
        <p className="text-lg md:text-2xl font-bold text-osrs-red">
          {formatGP(totalInvestment)}
        </p>
        <p className="text-xs text-gray-500 mt-1">
          Completed: {formatGP(stats.total_invested || 0)} | Pending: {formatGP(stats.pending_capital || 0)}
        </p>
      </div>

      <div className="card">
        <h3 className="text-sm text-gray-400 mb-2">Total Returned</h3>
        <p className="text-lg md:text-2xl font-bold text-osrs-green">
          {formatGP(totalReturned)}
        </p>
        <p className="text-xs text-gray-500 mt-1">From completed flips</p>
      </div>

      <div className="card">
        <h3 className="text-sm text-gray-400 mb-2">Net Profit</h3>
        <p className="text-lg md:text-2xl font-bold text-osrs-gold">
          {formatGP(netProfit)}
        </p>
        <p className="text-xs text-gray-500 mt-1">
          Completed: {formatGP(stats.total_profit || 0)} | Partial: {formatGP(stats.pending_profit || 0)}
        </p>
      </div>

      <div className="card">
        <h3 className="text-sm text-gray-400 mb-2">ROI Total</h3>
        <p className="text-lg md:text-2xl font-bold text-yellow-400">
          {formatPercent(stats.avg_roi || 0)}
        </p>
        <p className="text-xs text-gray-500 mt-1">From completed flips</p>
      </div>

      {hasProjection && (
        <div className="card border border-osrs-blue border-opacity-50">
          <h3 className="text-sm text-osrs-blue mb-2">Projected Profit</h3>
          <p className={`text-lg md:text-2xl font-bold ${projectedProfit > 0 ? 'text-osrs-green' : 'text-osrs-red'}`}>
            {formatGP(projectedProfit)}
          </p>
          <p className="text-xs text-gray-500 mt-1">If all pending sold at market</p>
        </div>
      )}

      {currentValue > 0 && (
        <div className="card border border-osrs-blue border-opacity-50">
          <h3 className="text-sm text-osrs-blue mb-2">Current Value</h3>
          <p className="text-lg md:text-2xl font-bold text-white">
            {formatGP(currentValue)}
          </p>
          <p className="text-xs text-gray-500 mt-1">Market value of pending items</p>
        </div>
      )}

      <div className="card">
        <h3 className="text-sm text-gray-400 mb-2">Success Rate</h3>
        <p className="text-lg md:text-2xl font-bold text-osrs-green">
          {stats.total_flips > 0 
            ? formatPercent((stats.winning_flips / stats.total_flips) * 100)
            : '0%'}
        </p>
      </div>

      <div className="card">
        <h3 className="text-sm text-gray-400 mb-2">Pending Flips</h3>
        <p className="text-lg md:text-2xl font-bold">{stats.pending_flips || 0}</p>
      </div>

      <div className="card">
        <h3 className="text-sm text-gray-400 mb-2">Completed Flips</h3>
        <p className="text-lg md:text-2xl font-bold">{stats.total_flips || 0}</p>
      </div>

      <div className="card">
        <h3 className="text-sm text-gray-400 mb-2">ROI In-Progress</h3>
        <p className="text-lg md:text-2xl font-bold text-osrs-green">
          {formatPercent(stats.roi_in_progress || 0)}
        </p>
        <p className="text-xs text-gray-500 mt-1">From partial sells</p>
      </div>
    </div>
  );
}