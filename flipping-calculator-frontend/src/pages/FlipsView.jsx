import { useState, useEffect } from 'react';
import { useFlipSearch, useTrendingFlips, useSettings } from '../hooks/useApi';
import { useAppStore } from '../stores/appStore';
import FlipSearchFilters from '../components/FlipSearchFilters';
import FlipTable from '../components/FlipTable';
import BuyModal from '../components/BuyModal';
import PriceHistoryModal from '../components/PriceHistoryModal';
import ItemSearchBar from '../components/ItemSearchBar';
import ItemDetailModal from '../components/ItemDetailModal';
import QuickFlipPresets from '../components/QuickFlipPresets';

export default function FlipsView() {
  const { filters, setFilters } = useAppStore();
  const { data: settings } = useSettings();
  const [searchParams, setSearchParams] = useState(null);
  const [trendingParams, setTrendingParams] = useState(null);
  const [selectedFlip, setSelectedFlip] = useState(null);
  const [priceHistoryItem, setPriceHistoryItem] = useState(null);
  const [detailItem, setDetailItem] = useState(null);

  // Sync cash filter with settings
  useEffect(() => {
    if (settings?.available_cash !== undefined) {
      setFilters({ cash: settings.available_cash });
    }
  }, [settings?.available_cash, setFilters]);

  const { data: searchData, isLoading: searchLoading, error: searchError } = useFlipSearch(searchParams);
  const { data: trendingData, isLoading: trendingLoading, error: trendingError } = useTrendingFlips(trendingParams);

  // Active mode: trending or regular search
  const isTrending = trendingParams && !searchParams;
  const data = isTrending ? trendingData : searchData;
  const isLoading = isTrending ? trendingLoading : searchLoading;
  const error = isTrending ? trendingError : searchError;

  const buildSearchParams = (overrides) => {
    const f = overrides || filters;
    return {
      min_profit: f.minProfit,
      min_limit_profit: f.minLimitProfit,
      min_volume: f.minVolume,
      min_roi: f.minRoi,
      max_roi: f.maxRoi,
      cash: f.cash,
      sort_by: f.sortBy ?? filters.sortBy,
      limit: f.limit ?? filters.limit,
      enable_quality_filter: f.enableQualityFilter ?? false,
      require_grindable: f.requireGrindable ?? false,
    };
  };

  const handleSearch = (overrides) => {
    setTrendingParams(null);
    setSearchParams(buildSearchParams(overrides));
  };

  const handleTrending = () => {
    setSearchParams(null);
    setTrendingParams({ cash: filters.cash, limit: 10 });
  };

  return (
    <div>
      <div className="card mb-4 md:mb-6">
        <h2 className="text-base md:text-lg font-bold text-osrs-gold mb-2 md:mb-3">Item Lookup</h2>
        <ItemSearchBar
          onSelectItem={(item) => {
            setDetailItem(item);
          }}
        />
      </div>

      <QuickFlipPresets onSearch={handleSearch} onTrending={handleTrending} />

      <FlipSearchFilters onSearch={() => handleSearch()} />

      {isLoading && (
        <div className="card text-center py-12">
          <p className="text-gray-400">{isTrending ? 'Finding trending items...' : 'Searching for flips...'}</p>
        </div>
      )}

      {error && (
        <div className="card text-center py-12">
          <p className="text-red-400">Error: {error.message}</p>
        </div>
      )}

      {!isLoading && !error && data && (
        <>
          <div className="mb-4 text-gray-400">
            {isTrending
              ? `Top ${data.flips?.length || 0} trending items by momentum`
              : `Found ${data.flips?.length || 0} profitable flips`
            }
          </div>
          <FlipTable 
            flips={data.flips} 
            onSelectFlip={setSelectedFlip}
            onShowPriceHistory={(item) => setPriceHistoryItem({ id: item.id, name: item.name })}
            onShowDetail={setDetailItem}
          />
        </>
      )}

      {selectedFlip && (
        <BuyModal
          flip={selectedFlip}
          onClose={() => setSelectedFlip(null)}
        />
      )}

      {priceHistoryItem && (
        <PriceHistoryModal
          isOpen={!!priceHistoryItem}
          itemId={priceHistoryItem.id}
          itemName={priceHistoryItem.name}
          onClose={() => setPriceHistoryItem(null)}
        />
      )}

      {detailItem && (
        <ItemDetailModal
          item={detailItem}
          onClose={() => setDetailItem(null)}
        />
      )}
    </div>
  );
}
