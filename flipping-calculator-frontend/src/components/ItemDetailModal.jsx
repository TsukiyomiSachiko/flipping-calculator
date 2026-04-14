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

  // If we already have full flip data (from the table), skip the fetch
  const hasFlipData = item?.buy_price != null;
  const { data: liveItem, isLoading, error } = useItemWithPrices(
    hasFlipData ? null : item?.id,
    filters.cash
  );

  if (!item) return null;

  // Use flip data if available, otherwise use the live fetched data
  const displayItem = hasFlipData ? item : liveItem;
  
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
            {!hasFlipData && isLoading && (
              <div className="text-center py-8 text-gray-400">Loading live prices...</div>
            )}

            {!hasFlipData && error && (
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