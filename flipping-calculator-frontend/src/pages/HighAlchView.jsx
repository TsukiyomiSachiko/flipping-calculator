import { useState, useMemo } from 'react';
import { useProfitableAlchs } from '../hooks/useApi';
import { formatNumber } from '../utils/formatters';
import LoadingSpinner from '../components/LoadingSpinner';

export default function HighAlchView() {
  const [searchTerm, setSearchTerm] = useState('');
  const [minVolume, setMinVolume] = useState(10); // Hide low-volume/untradeable items by default
  const [sortBy, setSortBy] = useState('profit_at_limit'); // 'profit_at_limit' | 'profit_per_alch' | 'roi' | 'volume_1h'
  const [sortOrder, setSortOrder] = useState('desc');

  const { data: alchItems, isLoading, error, refetch } = useProfitableAlchs(1); // Fetch all profitable items (min_volume=1)

  // Filter and sort items locally for smooth UX
  const processedItems = useMemo(() => {
    if (!alchItems) return [];

    return alchItems
      .filter(item => {
        const matchesSearch = item.name.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesVolume = item.volume_1h >= minVolume;
        return matchesSearch && matchesVolume;
      })
      .sort((a, b) => {
        let valA = a[sortBy];
        let valB = b[sortBy];

        // Handle null values
        if (valA === null || valA === undefined) valA = 0;
        if (valB === null || valB === undefined) valB = 0;

        if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
        if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
        return 0;
      });
  }, [alchItems, searchTerm, minVolume, sortBy, sortOrder]);

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  const SortIndicator = ({ field }) => {
    if (sortBy !== field) return <span className="text-luxury-purpleLight/40 ml-1">⇅</span>;
    return sortOrder === 'asc' ? <span className="text-luxury-gold ml-1">▲</span> : <span className="text-luxury-gold ml-1">▼</span>;
  };

  if (isLoading) {
    return (
      <div className="card flex justify-center py-12">
        <LoadingSpinner message="Loading profitable alchemy options..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="card text-center py-12 bg-red-950/20 border border-osrs-red/30 rounded-xl">
        <span className="text-4xl mb-4 block">⚠️</span>
        <p className="text-red-300 font-bold">Failed to load alchemy data: {error.message}</p>
        <button 
          onClick={() => refetch()}
          className="btn btn-secondary mt-6"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Description Card */}
      <div className="card p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl md:text-2xl font-black font-cinzel text-transparent bg-clip-text bg-gold-gradient tracking-wide mb-2">
            🔥 Profitable High Alchemy
          </h2>
          <p className="text-gray-400 text-sm max-w-2xl">
            Find items to buy on the Grand Exchange and High-Alch for a guaranteed profit. 
            All calculations assume zero GE tax (alchemy is tax-free) and include the dynamic cost of 1 Nature Rune.
          </p>
        </div>
        <div className="bg-[#0d0a1b] px-4 py-2.5 rounded-xl border border-luxury-border text-center md:text-right shrink-0">
          <span className="text-[10px] text-luxury-purpleLight/60 block uppercase font-bold tracking-widest">Nature Rune Cost</span>
          <span className="text-lg font-black text-luxury-gold font-outfit">
            {alchItems && alchItems.length > 0 ? formatNumber(alchItems[0].buy_price + alchItems[0].profit_per_alch - alchItems[0].highalch + (alchItems[0].buy_price * 0) || 90) : '90'} <span className="text-xs text-gray-400">gp</span>
          </span>
          <span className="text-[10px] text-gray-500 block mt-0.5">
            Dynamic Wiki Price: {alchItems && alchItems.length > 0 ? formatNumber(alchItems[0].highalch - alchItems[0].buy_price - alchItems[0].profit_per_alch) : '90'} gp
          </span>
        </div>
      </div>

      {/* Filter and Configuration Section */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="relative">
          <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 text-sm">🔍</span>
          <input
            type="text"
            className="input w-full pl-10"
            placeholder="Search items..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="bg-[#100c24]/40 border border-luxury-border/60 rounded-xl px-4 py-2 flex items-center justify-between">
          <span className="text-sm text-gray-400 font-medium">Min Hourly Volume:</span>
          <div className="flex items-center gap-2">
            <input
              type="number"
              min="0"
              className="w-20 input py-1 px-2 text-center font-bold text-luxury-gold focus:outline-none"
              value={minVolume}
              onChange={(e) => setMinVolume(Math.max(0, parseInt(e.target.value) || 0))}
            />
            <span className="text-xs text-gray-500 font-medium">/ hr</span>
          </div>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => refetch()}
            className="btn btn-secondary flex-1 flex items-center justify-center gap-2"
          >
            🔄 Refresh Prices
          </button>
        </div>
      </div>

      {/* Results Table */}
      <div className="luxury-table-container">
        <table className="luxury-table">
          <thead>
            <tr>
              <th className="py-4 px-4 select-none">Item</th>
              <th className="py-4 px-4 text-right cursor-pointer select-none" onClick={() => handleSort('highalch')}>
                High Alch <SortIndicator field="highalch" />
              </th>
              <th className="py-4 px-4 text-right cursor-pointer select-none" onClick={() => handleSort('buy_price')}>
                GE Buy (Slow) <SortIndicator field="buy_price" />
              </th>
              <th className="py-4 px-4 text-right cursor-pointer select-none" onClick={() => handleSort('profit_per_alch')}>
                Alch Profit <SortIndicator field="profit_per_alch" />
              </th>
              <th className="py-4 px-4 text-right cursor-pointer select-none" onClick={() => handleSort('roi')}>
                ROI <SortIndicator field="roi" />
              </th>
              <th className="py-4 px-4 text-right cursor-pointer select-none" onClick={() => handleSort('limit')}>
                GE Limit <SortIndicator field="limit" />
              </th>
              <th className="py-4 px-4 text-right cursor-pointer select-none" onClick={() => handleSort('profit_at_limit')}>
                Profit @ Limit <SortIndicator field="profit_at_limit" />
              </th>
              <th className="py-4 px-4 text-right cursor-pointer select-none" onClick={() => handleSort('volume_1h')}>
                1h Volume <SortIndicator field="volume_1h" />
              </th>
            </tr>
          </thead>
          <tbody>
            {processedItems.map((item) => (
              <tr key={item.id}>
                <td className="py-3.5 px-4">
                  <div className="flex items-center gap-3">
                    <div>
                      <span className="font-bold text-white block">{item.name}</span>
                      <div className="flex gap-1.5 mt-0.5">
                        {item.members && (
                          <span className="text-[9px] bg-luxury-purple/20 text-luxury-purpleLight px-1.5 py-0.5 rounded font-bold uppercase tracking-wide border border-luxury-purple/30">
                            Members
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </td>
                <td className="py-3.5 px-4 text-right font-semibold text-gray-300">
                  {formatNumber(item.highalch)} gp
                </td>
                <td className="py-3.5 px-4 text-right font-medium text-gray-400">
                  <span className="block">{formatNumber(item.buy_price)} gp</span>
                  {item.high_price && item.high_price !== item.buy_price && (
                    <span className="text-xs text-luxury-purpleLight/40 block mt-0.5">Instant: {formatNumber(item.high_price)} gp</span>
                  )}
                </td>
                <td className={`py-3.5 px-4 text-right font-black ${item.profit_per_alch > 0 ? 'text-osrs-green' : 'text-osrs-red'}`}>
                  +{formatNumber(item.profit_per_alch)} gp
                  {item.profit_instant !== null && item.profit_instant !== item.profit_per_alch && (
                    <span className={`text-xs block mt-0.5 font-normal ${item.profit_instant > 0 ? 'text-green-600' : 'text-red-600'}`}>
                      Instant: {item.profit_instant > 0 ? '+' : ''}{formatNumber(item.profit_instant)} gp
                    </span>
                  )}
                </td>
                <td className={`py-3.5 px-4 text-right font-bold ${item.roi > 0 ? 'text-osrs-green' : 'text-osrs-red'}`}>
                  {item.roi}%
                </td>
                <td className="py-3.5 px-4 text-right font-medium text-gray-300">
                  {formatNumber(item.limit)}
                </td>
                <td className={`py-3.5 px-4 text-right font-black text-base ${item.profit_at_limit > 0 ? 'text-osrs-green' : 'text-osrs-red'}`}>
                  {formatNumber(item.profit_at_limit)} gp
                </td>
                <td className="py-3.5 px-4 text-right font-semibold text-gray-400">
                  {formatNumber(item.volume_1h)}
                </td>
              </tr>
            ))}
            {processedItems.length === 0 && (
              <tr>
                <td colSpan="8" className="py-12 text-center text-luxury-purpleLight/60">
                  No profitable alchemy items found matching the search and volume criteria.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
