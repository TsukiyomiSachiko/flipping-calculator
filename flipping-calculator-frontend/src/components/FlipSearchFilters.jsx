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
    <div className="card mb-4 md:mb-6">
      <h2 className="text-lg md:text-2xl font-bold mb-3 md:mb-4 text-osrs-gold">Search Filters</h2>
      
      <div className="grid grid-cols-2 md:grid-cols-2 lg:grid-cols-3 gap-3 md:gap-4">
        <div>
          <label className="block text-sm font-medium mb-2">Min Profit</label>
          <input
            type="number"
            className="input w-full"
            value={filters.minProfit || ''}
            onChange={(e) => handleInputChange('minProfit', parseInt(e.target.value))}
            placeholder="100"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Min Limit Profit</label>
          <input
            type="text"
            className="input w-full"
            defaultValue={filters.minLimitProfit ? formatGP(filters.minLimitProfit) : ''}
            onBlur={(e) => handleGPInput('minLimitProfit', e)}
            placeholder="e.g., 500K, 1M"
          />
          <p className="text-xs text-gray-400 mt-1">Profit if buying GE limit. Supports K, M, B</p>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Min Volume</label>
          <input
            type="number"
            className="input w-full"
            value={filters.minVolume || ''}
            onChange={(e) => handleInputChange('minVolume', parseInt(e.target.value))}
            placeholder="5000"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Min ROI %</label>
          <input
            type="number"
            className="input w-full"
            value={filters.minRoi || ''}
            onChange={(e) => handleInputChange('minRoi', parseFloat(e.target.value))}
            placeholder="Optional"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Max ROI %</label>
          <input
            type="number"
            className="input w-full"
            value={filters.maxRoi || ''}
            onChange={(e) => handleInputChange('maxRoi', parseFloat(e.target.value))}
            placeholder="Optional"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Sort By</label>
          <select
            className="input w-full"
            value={filters.sortBy}
            onChange={(e) => setFilters({ sortBy: e.target.value })}
          >
            <option value="profit">Profit</option>
            <option value="roi">ROI %</option>
            <option value="volume">Volume</option>
            <option value="score">Score</option>
            <option value="erebus">Erebus Score</option>
            <option value="quality">Data Quality</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Limit</label>
          <input
            type="number"
            className="input w-full"
            value={filters.limit || ''}
            onChange={(e) => handleInputChange('limit', parseInt(e.target.value))}
            placeholder="20"
          />
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-gray-700">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={filters.enableQualityFilter || false}
            onChange={(e) => setFilters({ enableQualityFilter: e.target.checked })}
            className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-osrs-green focus:ring-osrs-green"
          />
          <span className="text-sm font-medium">
            Filter Suspicious Items
            <span className="text-xs text-gray-400 block">
              Removes likely manipulated data (extreme spreads, low volume spikes, statistical outliers)
            </span>
          </span>
        </label>
      </div>

      <div className="mt-4 flex gap-3">
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