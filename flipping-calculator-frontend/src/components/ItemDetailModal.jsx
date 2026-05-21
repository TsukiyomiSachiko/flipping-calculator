import { useState } from 'react';
import { useItemWithPrices } from '../hooks/useApi';
import { useAppStore } from '../stores/appStore';
import { formatGP, formatExactGP, formatPercent, getVolumeIndicator } from '../utils/formatters';
import PriceHistoryModal from './PriceHistoryModal';
import BuyModal from './BuyModal';
import MarketTrajectory from './MarketTrajectory';
import MarginChart from './MarginChart';
import LiquidityInsights from './LiquidityInsights';

export default function ItemDetailModal({ item, onClose }) {
  const [showPriceHistory, setShowPriceHistory] = useState(false);
  const [showBuyModal, setShowBuyModal] = useState(false);
  const [copiedPrice, setCopiedPrice] = useState(null);
  const { filters } = useAppStore();

  // Always fetch live data to enrich with long-term and high-alch stats
  const hasCachedPrices = item?.buy_price != null;
  const { data: liveItem, isLoading, error } = useItemWithPrices(
    item?.id,
    filters.cash
  );

  if (!item) return null;

  // Use live data if loaded, otherwise fall back to cached/props data
  const displayItem = liveItem || item;
  
  const copyPrice = (price, type) => {
    navigator.clipboard.writeText(price.toString());
    setCopiedPrice(type);
    setTimeout(() => setCopiedPrice(null), 2000);
  };

  return (
    <>
      <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-[60] p-2 md:p-4">
        <div className="bg-gray-800 rounded-lg w-full max-w-2xl border border-gray-700 max-h-[90vh] overflow-y-auto">
          {/* Header */}
          <div className="border-b border-gray-700 p-4 md:p-6 flex justify-between items-center">
            <div>
              <h2 className="text-lg md:text-2xl font-bold text-white">
                <a 
                  href={`https://oldschool.runescape.wiki/w/${encodeURIComponent(item.name)}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-osrs-gold transition-colors"
                  title="View on OSRS Wiki"
                >
                  {item.name}
                </a>
              </h2>
              <p className="text-sm text-gray-400 mt-1">
                {item.members
                  ? <span className="text-yellow-400">⭐ Members</span>
                  : <span>F2P</span>
                }
                {(item.ge_limit || item.ge_limit === 0) && (
                  <span className="ml-3">GE Limit: {item.ge_limit.toLocaleString()}</span>
                )}
              </p>
            </div>
            <button
              className="text-gray-400 hover:text-white text-2xl"
              onClick={onClose}
            >
              ✕
            </button>
          </div>

          {/* Content */}
          <div className="p-4 md:p-6">
            {!hasCachedPrices && isLoading && (
              <div className="text-center py-8 text-gray-400">Loading live prices...</div>
            )}

            {!hasCachedPrices && error && (
              <div className="text-center py-8 text-red-400">Failed to load prices.</div>
            )}

            {displayItem && displayItem.buy_price != null && (
              <>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4 mb-3 md:mb-4">
                  <div className="card relative">
                    <p className="text-xs text-gray-400 mb-1">Buy Price</p>
                    <p className="text-osrs-red font-bold">{formatExactGP(displayItem.buy_price)}</p>
                    <button 
                      onClick={() => copyPrice(displayItem.buy_price, 'buy')}
                      className="absolute top-2 right-2 text-gray-400 hover:text-white text-xs"
                      title="Copy to clipboard"
                    >
                      {copiedPrice === 'buy' ? '✓' : '📋'}
                    </button>
                  </div>
                  <div className="card relative">
                    <p className="text-xs text-gray-400 mb-1">Sell Price</p>
                    <p className="text-osrs-green font-bold">{formatExactGP(displayItem.sell_price)}</p>
                    <button 
                      onClick={() => copyPrice(displayItem.sell_price, 'sell')}
                      className="absolute top-2 right-2 text-gray-400 hover:text-white text-xs"
                      title="Copy to clipboard"
                    >
                      {copiedPrice === 'sell' ? '✓' : '📋'}
                    </button>
                  </div>
                  <DataCard label="Profit" value={formatExactGP(displayItem.profit)} color="text-osrs-gold" />
                  <DataCard label="ROI" value={formatPercent(displayItem.roi)} color={displayItem.roi >= 10 ? 'text-osrs-green' : displayItem.roi >= 5 ? 'text-yellow-400' : 'text-gray-400'} />
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4 mb-3 md:mb-4">
                  <DataCard label="Volume" value={(() => { const v = getVolumeIndicator(displayItem.volume); return `${v.emoji} ${displayItem.volume?.toLocaleString() || 'N/A'}`; })()} />
                  <DataCard label="GE Tax" value={formatGP(displayItem.ge_tax ?? (displayItem.sell_price > 50 ? Math.floor(displayItem.sell_price * 0.02) : 0))} color="text-osrs-red" />
                  <DataCard label="Max Qty (Cash)" value={displayItem.max_qty?.toLocaleString() || 'N/A'} />
                  <DataCard label="Your Profit" value={formatGP(displayItem.your_profit)} color="text-osrs-green" />
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3 md:gap-4">
                  <DataCard label="GE Limit" value={displayItem.ge_limit?.toLocaleString() || 'N/A'} />
                  <DataCard label="Profit at Limit" value={formatGP(displayItem.profit_at_limit)} color="text-blue-400" />
                  <DataCard
                    label="Score"
                    value={displayItem.score != null ? `${displayItem.score} / 100` : '—'}
                    color={
                      displayItem.score >= 70 ? 'text-osrs-green' :
                      displayItem.score >= 45 ? 'text-yellow-400' :
                      displayItem.score >= 25 ? 'text-orange-400' : 'text-gray-400'
                    }
                  />
                  <DataCard
                    label="Risk-Adj Score"
                    value={displayItem.risk_adjusted_score != null ? `${displayItem.risk_adjusted_score.toFixed(1)} / 100` : '—'}
                    color={
                      displayItem.risk_adjusted_score >= 70 ? 'text-osrs-green' :
                      displayItem.risk_adjusted_score >= 45 ? 'text-yellow-400' :
                      displayItem.risk_adjusted_score >= 25 ? 'text-orange-400' : 'text-gray-400'
                    }
                  />
                  <DataCard
                    label="Erebus Score"
                    value={displayItem.secondary_score != null ? displayItem.secondary_score : '—'}
                    color={
                      displayItem.secondary_score == null ? 'text-gray-500' :
                      displayItem.secondary_score >= 50 ? 'text-purple-400' :
                      displayItem.secondary_score >= 20 ? 'text-osrs-green' :
                      displayItem.secondary_score >= 5 ? 'text-yellow-400' : 'text-gray-400'
                    }
                  />
                </div>

                {/* Crash Risk Assessment */}
                <div className="mt-4 border-t border-gray-700 pt-4">
                  <h3 className="text-sm font-semibold text-osrs-gold mb-3 flex items-center gap-1.5">
                    <span>🛡️</span> Crash Risk Assessment
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
                    <DataCard
                      label="Crash Risk Score"
                      value={displayItem.crash_risk_score != null ? `${displayItem.crash_risk_score.toFixed(0)} / 100` : '—'}
                      color={
                        displayItem.crash_risk_score == null ? 'text-gray-400' :
                        displayItem.crash_risk_score < 35 ? 'text-osrs-green' :
                        displayItem.crash_risk_score <= 70 ? 'text-yellow-400' : 'text-osrs-red'
                      }
                    />
                    <DataCard
                      label="Max Drawdown (30d)"
                      value={displayItem.max_drawdown_30d != null ? `${displayItem.max_drawdown_30d.toFixed(1)}%` : '—'}
                      color="text-osrs-red"
                    />
                    <DataCard
                      label="Price Percentile (30d)"
                      value={displayItem.price_percentile_30d != null ? `${displayItem.price_percentile_30d.toFixed(1)}%` : '—'}
                      color={
                        displayItem.price_percentile_30d == null ? 'text-gray-400' :
                        displayItem.price_percentile_30d > 75 ? 'text-osrs-red' :
                        displayItem.price_percentile_30d > 40 ? 'text-yellow-400' : 'text-osrs-green'
                      }
                    />
                    <DataCard
                      label="Risk-to-Reward Ratio"
                      value={displayItem.risk_to_reward_ratio != null ? `${displayItem.risk_to_reward_ratio.toFixed(2)}x` : '—'}
                      color={
                        displayItem.risk_to_reward_ratio == null ? 'text-gray-400' :
                        displayItem.risk_to_reward_ratio > 3 ? 'text-osrs-red' :
                        displayItem.risk_to_reward_ratio > 1.5 ? 'text-yellow-400' : 'text-osrs-green'
                      }
                    />
                  </div>
                </div>

                {/* Long-Term Flipping Stats (7-Day Projection) */}
                <div className="mt-4 border-t border-gray-700 pt-4">
                  <h3 className="text-sm font-semibold text-osrs-gold mb-3 flex items-center gap-1.5">
                    <span>⏳</span> Long-Term Flipping Stats (7-Day Projection)
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
                    <DataCard
                      label="Expected Sell Price"
                      value={displayItem.expected_sell_price != null ? formatExactGP(displayItem.expected_sell_price) : '—'}
                      color="text-osrs-green"
                    />
                    <DataCard
                      label="Expected Profit"
                      value={displayItem.expected_profit_7d != null ? formatGP(displayItem.expected_profit_7d) : '—'}
                      color="text-osrs-gold"
                    />
                    <DataCard
                      label="Expected ROI"
                      value={displayItem.expected_roi_7d != null ? formatPercent(displayItem.expected_roi_7d) : '—'}
                      color={
                        displayItem.expected_roi_7d >= 10 ? 'text-osrs-green' :
                        displayItem.expected_roi_7d >= 5 ? 'text-yellow-400' :
                        displayItem.expected_roi_7d >= 0 ? 'text-gray-400' : 'text-osrs-red'
                      }
                    />
                    <DataCard
                      label="Long-Term Score"
                      value={displayItem.long_term_score != null ? `${displayItem.long_term_score} / 100` : '—'}
                      color={
                        displayItem.long_term_score >= 70 ? 'text-osrs-green' :
                        displayItem.long_term_score >= 45 ? 'text-yellow-400' :
                        displayItem.long_term_score >= 25 ? 'text-orange-400' : 'text-gray-400'
                      }
                    />
                  </div>
                </div>

                {/* High Alchemy Stats */}
                <div className="mt-4 border-t border-gray-700 pt-4">
                  <h3 className="text-sm font-semibold text-osrs-gold mb-3 flex items-center gap-1.5">
                    <span>🔥</span> High Alchemy Stats
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3 md:gap-4">
                    <DataCard
                      label="High Alch Value"
                      value={displayItem.highalch != null && displayItem.highalch > 0 ? formatExactGP(displayItem.highalch) : '—'}
                    />
                    <DataCard
                      label="Nature Rune Cost"
                      value={displayItem.nature_rune_price != null ? formatExactGP(displayItem.nature_rune_price) : '—'}
                      color="text-osrs-red"
                    />
                    <DataCard
                      label="High Alch Profit"
                      value={displayItem.highalch_profit != null ? formatExactGP(displayItem.highalch_profit) : '—'}
                      color={
                        displayItem.highalch_profit > 0 ? 'text-osrs-green' :
                        displayItem.highalch_profit < 0 ? 'text-osrs-red' : 'text-gray-400'
                      }
                    />
                  </div>
                </div>
              </>
            )}

            {displayItem && displayItem.buy_price == null && !isLoading && (
              <div className="text-center py-8 text-gray-400">No live price data available for this item.</div>
            )}

            {/* Market Trajectory */}
            {displayItem && displayItem.buy_price != null && (
              <div className="mt-3 md:mt-4">
                <MarketTrajectory itemId={item.id} itemName={item.name} compact={true} />
              </div>
            )}

            {/* Margin Chart */}
            {displayItem && displayItem.buy_price != null && (
              <div className="mt-3 md:mt-4">
                <MarginChart itemId={item.id} itemName={item.name} />
              </div>
            )}

            {/* Liquidity Insights */}
            {displayItem && displayItem.buy_price != null && (
              <div className="mt-3 md:mt-4">
                <LiquidityInsights itemId={item.id} itemName={item.name} />
              </div>
            )}

            {/* Action buttons */}
            <div className="flex gap-2 mt-4 md:mt-6">
              <button
                className="btn btn-primary flex-1"
                onClick={() => setShowBuyModal(true)}
                disabled={!displayItem || displayItem.buy_price == null}
              >
                🛒 Buy
              </button>
              <button
                className="btn btn-secondary flex-1"
                onClick={() => setShowPriceHistory(true)}
              >
                📈 Price History
              </button>
            </div>
          </div>
        </div>
      </div>

      {showPriceHistory && (
        <PriceHistoryModal
          isOpen={true}
          itemId={item.id}
          itemName={item.name}
          onClose={() => setShowPriceHistory(false)}
        />
      )}

      {showBuyModal && displayItem && (
        <BuyModal
          flip={displayItem}
          onClose={() => setShowBuyModal(false)}
        />
      )}
    </>
  );
}

function DataCard({ label, value, exact, color = 'text-white' }) {
  return (
    <div className="bg-gray-700 rounded p-3">
      <p className="text-xs text-gray-400 mb-1">{label}</p>
      <p className={`font-bold ${color}`}>{value}</p>
      {exact && <p className="text-xs text-gray-500">{exact}</p>}
    </div>
  );
}