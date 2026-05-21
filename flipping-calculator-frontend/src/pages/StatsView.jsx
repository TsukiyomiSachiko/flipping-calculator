import { useState } from 'react';
import { usePortfolioStatistics, usePortfolioSummary, useSettings, useSetCash } from '../hooks/useApi';
import { formatGP, formatPercent, parseCash } from '../utils/formatters';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useAppStore } from '../stores/appStore';
import ItemDetailModal from '../components/ItemDetailModal';
import SystemSettings from '../components/SystemSettings';
import CashflowSettings from '../components/CashflowSettings';
import LoadingSpinner from '../components/LoadingSpinner';

export default function StatsView() {
  const { data: stats, isLoading, error } = usePortfolioStatistics();
  const { data: summary } = usePortfolioSummary();
  const { data: settings } = useSettings();
  const setCashMutation = useSetCash();
  const [selectedItem, setSelectedItem] = useState(null);
  const [isEditingCash, setIsEditingCash] = useState(false);
  const [cashInput, setCashInput] = useState('');

  if (isLoading) {
    return <LoadingSpinner message="Loading statistics..." />;
  }

  if (error) {
    return (
      <div className="card text-center py-12 p-6">
        <p className="text-red-400 font-semibold font-outfit">Error loading statistics: {error.message}</p>
      </div>
    );
  }

  if (!stats) return null;

  const hasData = summary && summary.total_flips > 0;
  const availableCash = settings?.available_cash ?? summary?.available_cash ?? 0;
  
  const handleEditCash = () => {
    setCashInput(availableCash.toString());
    setIsEditingCash(true);
  };
  
  const handleSaveCash = () => {
    const amount = parseCash(cashInput);
    if (amount >= 0) {
      setCashMutation.mutate(amount);
      useAppStore.getState().setFilters({ cash: amount });
      setIsEditingCash(false);
    }
  };
  
  const handleCancelEdit = () => {
    setIsEditingCash(false);
    setCashInput('');
  };

  return (
    <>
      <div>
      <h2 className="text-xl md:text-2xl font-bold font-cinzel text-transparent bg-clip-text bg-gold-gradient tracking-wide mb-4 md:mb-6">Portfolio Dashboard</h2>

      <SystemSettings />

      {/* Overview Cards - Always shown */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 md:gap-4 mb-4 md:mb-6">
        <StatCard label="Total Volume Traded" value={stats.total_volume_traded?.toLocaleString() || '0'} sub="items" />
        <StatCard label="Total Turnover" value={formatGP(stats.total_turnover || 0)} sub="capital moved" />
        <StatCard
          label="Best Day"
          value={stats.best_day ? formatGP(stats.best_day.profit) : '—'}
          sub={stats.best_day?.day || ''}
          color={stats.best_day?.profit >= 0 ? 'text-osrs-green' : 'text-osrs-red'}
        />
        <div className="card p-4 md:p-5">
          <h3 className="text-xs text-luxury-purpleLight/60 font-semibold uppercase tracking-wider mb-2">Available Cash</h3>
          {isEditingCash ? (
            <div>
              <div className="flex gap-2 mb-1">
                <input
                  type="text"
                  className="input text-sm w-full"
                  value={cashInput}
                  onChange={(e) => setCashInput(e.target.value)}
                  placeholder="e.g. 10M, 500K, 1.5B"
                  autoFocus
                  onKeyPress={(e) => e.key === 'Enter' && handleSaveCash()}
                />
                <button className="btn btn-primary text-xs px-2.5 py-1" onClick={handleSaveCash}>✓</button>
                <button className="btn btn-secondary text-xs px-2.5 py-1" onClick={handleCancelEdit}>✗</button>
              </div>
              <p className="text-[10px] text-slate-400 font-outfit">Use K (thousand), M (million), or B (billion)</p>
            </div>
          ) : (
            <>
              <p className="text-lg md:text-2xl font-bold text-luxury-purpleLight hover:text-luxury-purpleLight/80 cursor-pointer transition-colors" onClick={handleEditCash}>
                {formatGP(availableCash)}
              </p>
              <p className="text-[10px] text-gray-500 font-outfit mt-1">Click to update</p>
            </>
          )}
        </div>
        <CashflowSettings />
      </div>

      {!hasData && (
        <div className="card text-center py-12 p-6">
          <p className="text-gray-400">No completed flips yet. Start flipping to see your stats!</p>
        </div>
      )}

      {hasData && (
        <>
          {/* Best & Worst Single Flips */}
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2 md:gap-4 mb-4 md:mb-6">
            {stats.best_single_flip && (
              <div className="card p-4 md:p-5">
                <h3 className="text-xs text-luxury-purpleLight/60 font-semibold uppercase tracking-wider mb-2">Best Single Flip</h3>
                <p className="text-lg font-bold font-cinzel text-luxury-gold cursor-pointer hover:text-luxury-goldBright transition-colors text-left" onClick={() => setSelectedItem({ id: stats.best_single_flip.item_id, name: stats.best_single_flip.item_name })}>{stats.best_single_flip.item_name}</p>
                <div className="flex flex-wrap gap-2 md:gap-4 mt-2 text-xs md:text-sm font-outfit">
                  <span className="text-osrs-green font-bold">{formatGP(stats.best_single_flip.profit)}</span>
                  <span className="text-gray-400">{stats.best_single_flip.quantity_total?.toLocaleString()}x</span>
                  <span className="text-yellow-400">{formatPercent(stats.best_single_flip.roi)} ROI</span>
                </div>
              </div>
            )}
            {stats.worst_single_flip && (
              <div className="card p-4 md:p-5">
                <h3 className="text-xs text-luxury-purpleLight/60 font-semibold uppercase tracking-wider mb-2">Worst Single Flip</h3>
                <p className="text-lg font-bold font-cinzel text-osrs-red cursor-pointer hover:text-red-400 transition-colors text-left" onClick={() => setSelectedItem({ id: stats.worst_single_flip.item_id, name: stats.worst_single_flip.item_name })}>{stats.worst_single_flip.item_name}</p>
                <div className="flex flex-wrap gap-2 md:gap-4 mt-2 text-xs md:text-sm font-outfit">
                  <span className="text-osrs-red font-bold">{formatGP(stats.worst_single_flip.profit)}</span>
                  <span className="text-gray-400">{stats.worst_single_flip.quantity_total?.toLocaleString()}x</span>
                  <span className={`${stats.worst_single_flip.roi >= 0 ? 'text-yellow-400' : 'text-osrs-red'}`}>{formatPercent(stats.worst_single_flip.roi)} ROI</span>
                </div>
              </div>
            )}
          </div>

          {/* Daily Profit Chart */}
          {stats.daily_profit?.length > 0 && (
            <div className="card p-4 md:p-6 mb-4 md:mb-6">
              <h3 className="text-lg font-bold font-cinzel text-transparent bg-clip-text bg-gold-gradient tracking-wide mb-4">Daily Profit (Last 30 Days)</h3>
              <div className="bg-[#0d0a1b]/60 border border-luxury-border/30 rounded-2xl p-4">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={stats.daily_profit}>
                    <defs>
                      <linearGradient id="goldGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#f3e5ab" />
                        <stop offset="50%" stopColor="#d4af37" />
                        <stop offset="100%" stopColor="#aa7c11" />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(139, 92, 246, 0.1)" />
                    <XAxis
                      dataKey="day"
                      stroke="#9CA3AF"
                      tickFormatter={(day) => {
                        const d = new Date(day + 'T00:00:00');
                        return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
                      }}
                    />
                    <YAxis stroke="#9CA3AF" tickFormatter={(v) => formatGP(v)} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0d0a1b', border: '1px solid rgba(139, 92, 246, 0.2)', borderRadius: '8px' }}
                      labelStyle={{ color: '#D1D5DB' }}
                      formatter={(value, name) => {
                        if (name === 'profit') return [formatGP(value), 'Profit'];
                        return [value, name];
                      }}
                      labelFormatter={(day) => new Date(day + 'T00:00:00').toLocaleDateString()}
                    />
                    <Bar
                      dataKey="profit"
                      fill="url(#goldGrad)"
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Item Tables */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6 mb-4 md:mb-6">
            {/* Best Performing Items */}
            <div className="card p-4 md:p-6">
              <h3 className="text-lg font-bold font-cinzel text-osrs-green mb-4">Top Performing Items</h3>
              {stats.best_items?.length > 0 ? (
                <div className="luxury-table-container">
                  <table className="luxury-table">
                    <thead>
                      <tr>
                        <th>Item</th>
                        <th className="text-right">Flips</th>
                        <th className="text-right">Total Profit</th>
                        <th className="text-right">Avg ROI</th>
                      </tr>
                    </thead>
                    <tbody>
                      {stats.best_items.map((item) => (
                        <tr key={item.item_name}>
                          <td>
                            <button
                              className="text-luxury-gold hover:text-luxury-goldBright font-semibold transition-colors text-left"
                              onClick={() => setSelectedItem({ id: item.item_id, name: item.item_name })}
                            >
                              {item.item_name}
                            </button>
                          </td>
                          <td className="text-right font-outfit">{item.flip_count}</td>
                          <td className={`text-right font-outfit font-bold ${item.total_profit >= 0 ? 'text-osrs-green' : 'text-osrs-red'}`}>{formatGP(item.total_profit)}</td>
                          <td className={`text-right font-outfit ${item.avg_roi >= 0 ? 'text-yellow-400' : 'text-osrs-red'}`}>{formatPercent(item.avg_roi)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-gray-400 text-sm italic">No data yet</p>
              )}
            </div>

            {/* Worst Performing Items */}
            <div className="card p-4 md:p-6">
              <h3 className="text-lg font-bold font-cinzel text-osrs-red mb-4">Worst Performing Items</h3>
              {stats.worst_items?.length > 0 ? (
                <div className="luxury-table-container">
                  <table className="luxury-table">
                    <thead>
                      <tr>
                        <th>Item</th>
                        <th className="text-right">Flips</th>
                        <th className="text-right">Total Profit</th>
                        <th className="text-right">Avg ROI</th>
                      </tr>
                    </thead>
                    <tbody>
                      {stats.worst_items.map((item) => (
                        <tr key={item.item_name}>
                          <td>
                            <button
                              className="text-luxury-gold hover:text-luxury-goldBright font-semibold transition-colors text-left"
                              onClick={() => setSelectedItem({ id: item.item_id, name: item.item_name })}
                            >
                              {item.item_name}
                            </button>
                          </td>
                          <td className="text-right font-outfit">{item.flip_count}</td>
                          <td className={`text-right font-outfit font-bold ${item.total_profit >= 0 ? 'text-osrs-green' : 'text-osrs-red'}`}>{formatGP(item.total_profit)}</td>
                          <td className={`text-right font-outfit ${item.avg_roi >= 0 ? 'text-yellow-400' : 'text-osrs-red'}`}>{formatPercent(item.avg_roi)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-gray-400 text-sm italic">No data yet</p>
              )}
            </div>
          </div>

          {/* Most Traded & Members Breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
            {/* Most Traded */}
            <div className="card p-4 md:p-6">
              <h3 className="text-lg font-bold font-cinzel text-transparent bg-clip-text bg-gold-gradient tracking-wide mb-4">Most Traded Items</h3>
              {stats.most_traded?.length > 0 ? (
                <div className="luxury-table-container">
                  <table className="luxury-table">
                    <thead>
                      <tr>
                        <th>Item</th>
                        <th className="text-right">Flips</th>
                        <th className="text-right">Qty Traded</th>
                        <th className="text-right">Total Profit</th>
                      </tr>
                    </thead>
                    <tbody>
                      {stats.most_traded.map((item) => (
                        <tr key={item.item_name}>
                          <td>
                            <button
                              className="text-luxury-gold hover:text-luxury-goldBright font-semibold transition-colors text-left"
                              onClick={() => setSelectedItem({ id: item.item_id, name: item.item_name })}
                            >
                              {item.item_name}
                            </button>
                          </td>
                          <td className="text-right font-outfit">{item.flip_count}</td>
                          <td className="text-right font-outfit">{item.total_quantity?.toLocaleString()}</td>
                          <td className={`text-right font-outfit font-bold ${item.total_profit >= 0 ? 'text-osrs-green' : 'text-osrs-red'}`}>{formatGP(item.total_profit)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-gray-400 text-sm italic">No data yet</p>
              )}
            </div>

            {/* Members vs F2P */}
            <div className="card p-4 md:p-6">
              <h3 className="text-lg font-bold font-cinzel text-transparent bg-clip-text bg-gold-gradient tracking-wide mb-4">Members vs F2P</h3>
              {stats.members_breakdown?.length > 0 ? (
                <div className="space-y-4">
                  {stats.members_breakdown.map((cat) => (
                    <div key={cat.category} className="bg-[#120e24]/60 border border-luxury-border/30 rounded-xl p-4 font-outfit">
                      <div className="flex justify-between items-center mb-2">
                        <span className="font-cinzel text-sm text-luxury-gold font-bold">
                          {cat.category === 'Members' ? '⭐ ' : ''}{cat.category}
                        </span>
                        <span className="text-luxury-purpleLight/60 text-xs font-semibold">{cat.flip_count} flips</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className={cat.total_profit >= 0 ? 'text-osrs-green font-medium' : 'text-osrs-red font-medium'}>{formatGP(cat.total_profit)} profit</span>
                        <span className={cat.avg_roi >= 0 ? 'text-yellow-400' : 'text-osrs-red'}>{formatPercent(cat.avg_roi)} avg ROI</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-400 text-sm italic">No data yet</p>
              )}
            </div>
          </div>
        </>
      )}
    </div>

      {selectedItem && (
        <ItemDetailModal
          item={selectedItem}
          onClose={() => setSelectedItem(null)}
        />
      )}
    </>
  );
}

function StatCard({ label, value, sub, color = 'text-white' }) {
  return (
    <div className="card p-4 md:p-5 flex flex-col justify-between">
      <div>
        <h3 className="text-xs text-luxury-purpleLight/60 font-semibold uppercase tracking-wider mb-2">{label}</h3>
        <p className={`text-lg md:text-2xl font-bold font-outfit ${color}`}>{value}</p>
      </div>
      {sub && <p className="text-xs text-gray-500 font-outfit mt-1">{sub}</p>}
    </div>
  );
}