import { useAppStore } from '../stores/appStore';

const PRESETS = [
  {
    label: '💰 Top 5 Under 1M',
    description: 'Best profit, good volume',
    filters: { minProfit: 0, minVolume: 5000, minRoi: null, maxRoi: null, minLimitProfit: null, sortBy: 'profit', limit: 5 },
  },
  {
    label: '🟢 High Volume',
    description: 'Active items, fast fills',
    filters: { minVolume: 50000, minProfit: 0, minRoi: null, maxRoi: null, minLimitProfit: null, sortBy: 'volume', limit: 10 },
  },
  {
    label: '⚡ Quick ROI',
    description: 'High ROI, lower capital',
    filters: { minRoi: 5, maxRoi: 25, minProfit: 0, minVolume: 1000, minLimitProfit: null, sortBy: 'roi', limit: 10 },
  },
  {
    label: '🏭 Limit Grinders',
    description: 'High-volume items (limit ≥ 50, vol ≥ 10% of limit)',
    filters: { minProfit: 10, minVolume: 0, minRoi: null, maxRoi: null, minLimitProfit: null, sortBy: 'limit', limit: 10, requireGrindable: true },
  },
  {
    label: '⭐ Best Score',
    description: 'Top composite score',
    filters: { minProfit: 0, minVolume: 0, minRoi: null, maxRoi: null, minLimitProfit: null, sortBy: 'score', limit: 10 },
  },
  {
    label: '🕐 Peak Times',
    description: 'Best flips in peak hours',
    filters: { minProfit: 0, minVolume: 5000, minRoi: null, maxRoi: null, minLimitProfit: null, sortBy: 'score', limit: 10 },
  },
];

export default function QuickFlipPresets({ onSearch, onTrending }) {
  const { setFilters } = useAppStore();

  const handlePreset = (preset) => {
    setFilters(preset.filters);

    // Trigger search immediately with the new filters
    setTimeout(() => onSearch(preset.filters), 0);
  };

  return (
    <div className="card mb-4 md:mb-6">
      <h2 className="text-base md:text-lg font-bold text-osrs-gold mb-2 md:mb-3">Quick Presets</h2>
      <div className="grid grid-cols-2 md:flex md:flex-wrap gap-2">
        {PRESETS.map((preset) => (
          <button
            key={preset.label}
            className="bg-gray-700 hover:bg-gray-600 text-white px-3 md:px-4 py-2 rounded-lg text-xs md:text-sm transition-colors group relative text-center"
            onClick={() => handlePreset(preset)}
          >
            {preset.label}
            <span className="hidden md:block absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-black text-xs text-gray-300 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
              {preset.description}
            </span>
          </button>
        ))}
        <button
          className="bg-gray-700 hover:bg-gray-600 text-white px-3 md:px-4 py-2 rounded-lg text-xs md:text-sm transition-colors group relative text-center"
          onClick={onTrending}
        >
          📈 Trending
          <span className="hidden md:block absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-black text-xs text-gray-300 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
            Top 10 by price momentum
          </span>
        </button>
      </div>
    </div>
  );
}