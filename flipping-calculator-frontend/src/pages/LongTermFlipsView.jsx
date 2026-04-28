import { useState, useEffect } from 'react';
import { useFlipSearch, useSettings } from '../hooks/useApi';
import { useAppStore } from '../stores/appStore';
import LongTermFlipTable from '../components/LongTermFlipTable';
import BuyModal from '../components/BuyModal';
import PriceHistoryModal from '../components/PriceHistoryModal';
import ItemSearchBar from '../components/ItemSearchBar';
import ItemDetailModal from '../components/ItemDetailModal';

export default function LongTermFlipsView() {
  const { filters } = useAppStore();
  const { data: settings } = useSettings();
  const [selectedFlip, setSelectedFlip] = useState(null);
  const [priceHistoryItem, setPriceHistoryItem] = useState(null);
  const [detailItem, setDetailItem] = useState(null);

  const searchParams = {
    sort_by: 'long_term',
    limit: 50,
    cash: settings?.available_cash || filters.cash,
    min_volume: 1000,
  };

  const { data: searchData, isLoading: searchLoading, error: searchError } = useFlipSearch(searchParams);

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

      <div className="card mb-4 md:mb-6">
        <h2 className="text-lg font-bold text-osrs-gold">Long-Term Flips</h2>
        <p className="text-sm text-gray-400 mt-2">
          These items are selected based on their 7-day price trajectory and stability, designed for holding over 3-14 days. Expected values assume the current market trends hold stable.
        </p>
      </div>

      {searchLoading && (
        <div className="card text-center py-12">
          <p className="text-gray-400">Searching for long-term flips...</p>
        </div>
      )}

      {searchError && (
        <div className="card text-center py-12">
          <p className="text-red-400">Error: {searchError.message}</p>
        </div>
      )}

      {!searchLoading && !searchError && searchData && (
        <>
          <div className="mb-4 text-gray-400">
            Found {searchData.flips?.length || 0} potential long-term investments
          </div>
          <LongTermFlipTable 
            flips={searchData.flips} 
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
