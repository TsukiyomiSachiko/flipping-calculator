import { useAppStore } from '../stores/appStore';
import { formatGP, parseCash } from '../utils/formatters';

export default function FlipSearchFilters({ onSearch }) {
  const { filters, setFilters } = useAppStore();

  const handleInputChange = (field, value) => {
    setFilters({ [field]: value === '' ? null : value });
  };

  const handleGPInput = (field, e) => {
    const parsed = parseCash(e.target.value);
    setFilters({ [field]: parsed || null });
  };

  return (
    <div className="card mb-4 md:mb-6 p-4 md:p-6">
      <h2 className="text-lg md:text-2xl font-bold mb-4 md:mb-6 bg-gold-gradient bg-clip-text text-transparent">
        Search Filters
      </h2>
      
      <div className="grid grid-cols-2 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-luxury-purpleLight mb-2">Min Profit</label>
          <input
            type="number"
            className="input w-full"
            value={filters.minProfit || ''}
            onChange={(e) => handleInputChange('minProfit', parseInt(e.target.value))}
            placeholder="100"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-luxury-purpleLight mb-2">Min Limit Profit</label>
          <input
            type="text"
            className="input w-full"
            defaultValue={filters.minLimitProfit ? formatGP(filters.minLimitProfit) : ''}
            onBlur={(e) => handleGPInput('minLimitProfit', e)}
            placeholder="e.g., 500K, 1M"
          />
          <p className="text-[10px] text-gray-400 mt-1.5 leading-relaxed">Profit if buying GE limit. Supports K, M, B</p>
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-luxury-purpleLight mb-2">Min Volume</label>
          <input
            type="number"
            className="input w-full"
            value={filters.minVolume || ''}
            onChange={(e) => handleInputChange('minVolume', parseInt(e.target.value))}
            placeholder="5000"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-luxury-purpleLight mb-2">Min ROI %</label>
          <input
            type="number"
            className="input w-full"
            value={filters.minRoi || ''}
            onChange={(e) => handleInputChange('minRoi', parseFloat(e.target.value))}
            placeholder="Optional"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-luxury-purpleLight mb-2">Max ROI %</label>
          <input
            type="number"
            className="input w-full"
            value={filters.maxRoi || ''}
            onChange={(e) => handleInputChange('maxRoi', parseFloat(e.target.value))}
            placeholder="Optional"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-luxury-purpleLight mb-2">Sort By</label>
          <select
            className="input w-full cursor-pointer"
            value={filters.sortBy}
            onChange={(e) => setFilters({ sortBy: e.target.value })}
          >
            <option value="profit" className="bg-luxury-darker text-white">Profit</option>
            <option value="roi" className="bg-luxury-darker text-white">ROI %</option>
            <option value="volume" className="bg-luxury-darker text-white">Volume</option>
            <option value="score" className="bg-luxury-darker text-white">Score</option>
            <option value="risk_adjusted" className="bg-luxury-darker text-white">Risk-Adjusted Score</option>
            <option value="crash_risk" className="bg-luxury-darker text-white">Crash Risk</option>
            <option value="risk_reward" className="bg-luxury-darker text-white">Risk/Reward Ratio</option>
            <option value="erebus" className="bg-luxury-darker text-white">Erebus Score</option>
            <option value="quality" className="bg-luxury-darker text-white">Data Quality</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-luxury-purpleLight mb-2">Limit</label>
          <input
            type="number"
            className="input w-full"
            value={filters.limit || ''}
            onChange={(e) => handleInputChange('limit', parseInt(e.target.value))}
            placeholder="20"
          />
        </div>
      </div>

      <div className="mt-5 pt-5 border-t border-luxury-border">
        <label className="flex items-start gap-3 cursor-pointer group">
          <div className="relative flex items-center h-5">
            <input
              type="checkbox"
              id="quality-filter"
              checked={filters.enableQualityFilter || false}
              onChange={(e) => setFilters({ enableQualityFilter: e.target.checked })}
              className="w-4 h-4 rounded border-luxury-purple/30 bg-luxury-darker/60 text-luxury-gold focus:ring-luxury-gold focus:ring-offset-luxury-dark cursor-pointer transition-colors duration-200"
            />
          </div>
          <span className="text-sm font-medium text-white group-hover:text-luxury-purpleLight transition-colors duration-200">
            Filter Suspicious Items
            <span className="text-xs text-gray-400 block mt-0.5 leading-relaxed font-normal">
              Removes likely manipulated data (extreme spreads, low volume spikes, statistical outliers)
            </span>
          </span>
        </label>
      </div>

      <div className="mt-6 flex gap-3">
        <button 
          className="btn btn-primary"
          onClick={onSearch}
        >
          Search Flips
        </button>
        <button 
          className="btn btn-secondary"
          onClick={() => useAppStore.getState().resetFilters()}
        >
          Reset Filters
        </button>
      </div>
    </div>
  );
}