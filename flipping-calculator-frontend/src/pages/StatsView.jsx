import { useState } from 'react';
import { usePortfolioStatistics, usePortfolioSummary, useSettings, useSetCash } from '../hooks/useApi';
import { formatGP, formatPercent, parseCash } from '../utils/formatters';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useAppStore } from '../stores/appStore';
import ItemDetailModal from '../components/ItemDetailModal';
import SystemSettings from '../components/SystemSettings';

export default function StatsView() {
  const { data: stats, isLoading, error } = usePortfolioStatistics();
  const { data: summary } = usePortfolioSummary();
  const { data: settings } = useSettings();
  const setCashMutation = useSetCash();
  const [selectedItem, setSelectedItem] = useState(null);
  const [isEditingCash, setIsEditingCash] = useState(false);
  const [cashInput, setCashInput] = useState('');

  if (isLoading) {
    return (
      <div className="card text-center py-12">
        <p className="text-gray-400">Loading statistics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card text-center py-12">
        <p className="text-red-400">Error loading statistics: {error.message}</p>
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
      <h2 className="text-lg md:text-2xl font-bold text-osrs-gold mb-4 md:mb-6">Portfolio Dashboard</h2>

      <SystemSettings />

      {/* Overview Cards - Always shown */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4 mb-4 md:mb-6">
        <StatCard label="Total Volume Traded" value={stats.total_volume_traded?.toLocaleString() || '0'} sub="items" />
        <StatCard label="Total Turnover" value={formatGP(stats.total_turnover || 0)} sub="capital moved" />
        <StatCard
          label="Best Day"
          value={stats.best_day ? formatGP(stats.best_day.profit) : '—'}
          sub={stats.best_day?.day || ''}
          color={stats.best_day?.profit >= 0 ? 'text-osrs-green' : 'text-osrs-red'}
        />
        <div className="card">
          <h3 className="text-sm text-gray-400 mb-2">Available Cash</h3>
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
                <button className="btn btn-primary text-xs px-2" onClick={handleSaveCash}>✓</button>
                <button className="btn btn-secondary text-xs px-2" onClick={handleCancelEdit}>✗</button>
              </div>
              <p className="text-xs text-slate-400">Use K (thousand), M (million), or B (billion)</p>
            </div>
          ) : (
            <>
              <p className="text-lg md:text-2xl font-bold text-osrs-blue cursor-pointer" onClick={handleEditCash}>
                {formatGP(availableCash)}
              </p>
              <p className="text-xs text-gray-500 mt-1">Click to update</p>
            </>
          )}
        </div>
      </div>

      {!hasData && (
        <div className="card text-center py-12">
          <p className="text-gray-400">No completed flips yet. Start flipping to see your stats!</p>
        </div>
      )}

      {hasData && (
        <>
          {/* Best & Worst Single Flips */}
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2 md:gap-4 mb-4 md:mb-6">
            {stats.best_single_flip && (
              <div className="card">
                <h3 className="text-sm text-gray-400 mb-2">Best Single Flip</h3>
                <p className="text-lg font-bold text-osrs-gold cursor-pointer hover:underline" onClick={() => setSelectedItem({ id: stats.best_single_flip.item_id, name: stats.best_single_flip.item_name })}>{stats.best_single_flip.item_name}</p>
                <div className="flex flex-wrap gap-2 md:gap-4 mt-2 text-xs md:text-sm">
                  <span className="text-osrs-green font-bold">{formatGP(stats.best_single_flip.profit)}</span>
                  <span className="text-gray-400">{stats.best_single_flip.quantity_total?.toLocaleString()}x</span>
                  <span className="text-yellow-400">{formatPercent(stats.best_single_flip.roi)} ROI</span>
                </div>
              </div>
            )}
            {stats.worst_single_flip && (
              <div className="card">
                <h3 className="text-sm text-gray-400 mb-2">Worst Single Flip</h3>
                <p className="text-lg font-bold text-osrs-red cursor-pointer hover:underline" onClick={() => setSelectedItem({ id: stats.worst_single_flip.item_id, name: stats.worst_single_flip.item_name })}>{stats.worst_single_flip.item_name}</p>
                <div className="flex flex-wrap gap-2 md:gap-4 mt-2 text-xs md:text-sm">
                  <span className="text-osrs-red font-bold">{formatGP(stats.worst_single_flip.profit)}</span>
                  <span className="text-gray-400">{stats.worst_single_flip.quantity_total?.toLocaleString()}x</span>
                  <span className={`${stats.worst_single_flip.roi >= 0 ? 'text-yellow-400' : 'text-osrs-red'}`}>{formatPercent(stats.worst_single_flip.roi)} ROI</span>
                </div>
              </div>
            )}
          </div>

          {/* Daily Profit Chart */}
          {stats.daily_profit?.length > 0 && (
            <div className="card mb-4 md:mb-6">
              <h3 className="text-lg font-bold text-osrs-gold mb-4">Daily Profit (Last 30 Days)</h3>
              <div className="bg-gray-900 rounded-lg p-4">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={stats.daily_profit}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
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
                      contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }}
                      labelStyle={{ color: '#D1D5DB' }}
                      formatter={(value, name) => {
                        if (name === 'profit') return [formatGP(value), 'Profit'];
                        return [value, name];
                      }}
                      labelFormatter={(day) => new Date(day + 'T00:00:00').toLocaleDateString()}
                    />
                    <Bar
                      dataKey="profit"
                      fill="#FFA500"
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
            <div className="card">
              <h3 className="text-lg font-bold text-osrs-green mb-4">Top Performing Items</h3>
              {stats.best_items?.length > 0 ? (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-700 text-gray-400">
                      <th className="text-left p-2">Item</th>
                      <th className="text-right p-2">Flips</th>
                      <th className="text-right p-2">Total Profit</th>
                      <th className="text-right p-2">Avg ROI</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.best_items.map((item) => (
                      <tr key={item.item_name} className="border-b border-gray-700">
                        <td className="p-2 text-osrs-gold cursor-pointer hover:underline" onClick={() => setSelectedItem({ id: item.item_id, name: item.item_name })}>{item.item_name}</td>
                        <td className="p-2 text-right">{item.flip_count}</td>
                        <td className={`p-2 text-right font-bold ${item.total_profit >= 0 ? 'text-osrs-green' : 'text-osrs-red'}`}>{formatGP(item.total_profit)}</td>
                        <td className={`p-2 text-right ${item.avg_roi >= 0 ? 'text-yellow-400' : 'text-osrs-red'}`}>{formatPercent(item.avg_roi)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="text-gray-400 text-sm">No data yet</p>
              )}
            </div>

            {/* Worst Performing Items */}
            <div className="card">
              <h3 className="text-lg font-bold text-osrs-red mb-4">Worst Performing Items</h3>
              {stats.worst_items?.length > 0 ? (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-700 text-gray-400">
                      <th className="text-left p-2">Item</th>
                      <th className="text-right p-2">Flips</th>
                      <th className="text-right p-2">Total Profit</th>
                      <th className="text-right p-2">Avg ROI</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.worst_items.map((item) => (
                      <tr key={item.item_name} className="border-b border-gray-700">
                        <td className="p-2 text-osrs-gold cursor-pointer hover:underline" onClick={() => setSelectedItem({ id: item.item_id, name: item.item_name })}>{item.item_name}</td>
                        <td className="p-2 text-right">{item.flip_count}</td>
                        <td className={`p-2 text-right font-bold ${item.total_profit >= 0 ? 'text-osrs-green' : 'text-osrs-red'}`}>{formatGP(item.total_profit)}</td>
                        <td className={`p-2 text-right ${item.avg_roi >= 0 ? 'text-yellow-400' : 'text-osrs-red'}`}>{formatPercent(item.avg_roi)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="text-gray-400 text-sm">No data yet</p>
              )}
            </div>
          </div>

          {/* Most Traded & Members Breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
            {/* Most Traded */}
            <div className="card">
              <h3 className="text-lg font-bold text-osrs-gold mb-4">Most Traded Items</h3>
              {stats.most_traded?.length > 0 ? (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-700 text-gray-400">
                      <th className="text-left p-2">Item</th>
                      <th className="text-right p-2">Flips</th>
                      <th className="text-right p-2">Qty Traded</th>
                      <th className="text-right p-2">Total Profit</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.most_traded.map((item) => (
                      <tr key={item.item_name} className="border-b border-gray-700">
                        <td className="p-2 text-osrs-gold cursor-pointer hover:underline" onClick={() => setSelectedItem({ id: item.item_id, name: item.item_name })}>{item.item_name}</td>
                        <td className="p-2 text-right">{item.flip_count}</td>
                        <td className="p-2 text-right">{item.total_quantity?.toLocaleString()}</td>
                        <td className={`p-2 text-right font-bold ${item.total_profit >= 0 ? 'text-osrs-green' : 'text-osrs-red'}`}>{formatGP(item.total_profit)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="text-gray-400 text-sm">No data yet</p>
              )}
            </div>

            {/* Members vs F2P */}
            <div className="card">
              <h3 className="text-lg font-bold text-osrs-gold mb-4">Members vs F2P</h3>
              {stats.members_breakdown?.length > 0 ? (
                <div className="space-y-4">
                  {stats.members_breakdown.map((cat) => (
                    <div key={cat.category} className="bg-gray-700 rounded p-4">
                      <div className="flex justify-between items-center mb-2">
                        <span className="font-bold">
                          {cat.category === 'Members' ? '⭐ ' : ''}{cat.category}
                        </span>
                        <span className="text-gray-400">{cat.flip_count} flips</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className={cat.total_profit >= 0 ? 'text-osrs-green' : 'text-osrs-red'}>{formatGP(cat.total_profit)} profit</span>
                        <span className={cat.avg_roi >= 0 ? 'text-yellow-400' : 'text-osrs-red'}>{formatPercent(cat.avg_roi)} avg ROI</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-400 text-sm">No data yet</p>
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
    <div className="card">
      <h3 className="text-xs md:text-sm text-gray-400 mb-1 md:mb-2">{label}</h3>
      <p className={`text-lg md:text-2xl font-bold ${color}`}>{value}</p>
      {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
    </div>
  );
}