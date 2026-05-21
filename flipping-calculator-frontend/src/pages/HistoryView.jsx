import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useCompletedFlips, useMutations } from '../hooks/useApi';
import { portfolioApi } from '../services/api';
import PriceHistoryModal from '../components/PriceHistoryModal';
import ConfirmModal from '../components/ConfirmModal';
import LoadingSpinner from '../components/LoadingSpinner';
import { formatGP, formatExactGP, formatPercent, formatDateTime } from '../utils/formatters';

export default function HistoryView() {
  const [activeTab, setActiveTab] = useState('completed'); // completed, mutations
  const { data: completedData, isLoading: isLoadingCompleted } = useCompletedFlips();
  const { data: mutationsData, isLoading: isLoadingMutations } = useMutations(100);
  
  const [sortBy, setSortBy] = useState('date'); // date, profit, roi
  const [priceHistoryItem, setPriceHistoryItem] = useState(null);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [flipToDelete, setFlipToDelete] = useState(null);
  const queryClient = useQueryClient();

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: portfolioApi.deleteFlip,
    onSuccess: () => {
      queryClient.invalidateQueries(['portfolio']);
      setDeleteModalOpen(false);
      setFlipToDelete(null);
    },
    onError: (error) => {
      alert(`Failed to delete flip: ${error.message}`);
    }
  });

  const handleDeleteClick = (flipId, itemName) => {
    setFlipToDelete({ id: flipId, name: itemName });
    setDeleteModalOpen(true);
  };

  const handleDeleteConfirm = () => {
    if (flipToDelete) {
      deleteMutation.mutate(flipToDelete.id);
    }
  };

  if (isLoadingCompleted || isLoadingMutations) {
    return <LoadingSpinner message="Loading History..." />;
  }

  // Sort completed flips
  const sortedCompleted = [...(completedData || [])].sort((a, b) => {
    if (sortBy === 'profit') {
      return (b.profit || 0) - (a.profit || 0);
    } else if (sortBy === 'roi') {
      return (b.roi || 0) - (a.roi || 0);
    } else {
      return new Date(b.sell_time || b.buy_time) - new Date(a.sell_time || a.buy_time);
    }
  });

  return (
    <div>
      <div className="flex gap-2 mb-6">
        <button
          className={`px-6 py-2.5 rounded-xl font-bold transition-all duration-300 flex items-center gap-2 ${
            activeTab === 'completed'
              ? 'bg-gold-gradient text-luxury-darker font-bold shadow-gold-glow scale-[1.03]'
              : 'bg-[#151128] hover:bg-[#20193d] text-gray-300 hover:text-white border border-luxury-border/60 hover:border-luxury-gold/30 hover:-translate-y-0.5'
          }`}
          onClick={() => setActiveTab('completed')}
        >
          🏆 Completed Flips
        </button>
        <button
          className={`px-6 py-2.5 rounded-xl font-bold transition-all duration-300 flex items-center gap-2 ${
            activeTab === 'mutations'
              ? 'bg-gold-gradient text-luxury-darker font-bold shadow-gold-glow scale-[1.03]'
              : 'bg-[#151128] hover:bg-[#20193d] text-gray-300 hover:text-white border border-luxury-border/60 hover:border-luxury-gold/30 hover:-translate-y-0.5'
          }`}
          onClick={() => setActiveTab('mutations')}
        >
          📜 Mutation Log
        </button>
      </div>

      {activeTab === 'completed' ? (
        <>
          <div className="card p-4 md:p-6 mb-4 md:mb-6">
            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2">
              <h2 className="text-xl md:text-2xl font-bold font-cinzel text-transparent bg-clip-text bg-gold-gradient tracking-wide">Flip History</h2>
              <div className="flex gap-2 items-center">
                <label className="text-sm text-luxury-purpleLight/80 font-medium">Sort:</label>
                <select
                  className="input flex-1 sm:flex-none"
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                >
                  <option value="date">Date</option>
                  <option value="profit">Profit</option>
                  <option value="roi">ROI</option>
                </select>
              </div>
            </div>
          </div>

          {sortedCompleted.length === 0 ? (
            <div className="card text-center py-12 p-6">
              <p className="text-gray-400">No completed flips yet. Complete a flip to see it here!</p>
            </div>
          ) : (
            <div className="space-y-3 md:space-y-4">
              {sortedCompleted.map((flip) => {
                const profitColor = flip.profit >= 0 ? 'text-osrs-green font-semibold' : 'text-osrs-red font-semibold';
                const roiColor = flip.roi >= 10 ? 'text-osrs-green' : 
                               flip.roi >= 5 ? 'text-yellow-400' : 'text-gray-400';
                
                const isPartial = flip.status === 'partially_completed';
                const cardBorder = isPartial ? 'border-l-4 border-l-luxury-gold' : 'border-l-4 border-l-luxury-purple';
                
                return (
                  <div key={flip.id} className={`card ${cardBorder} p-4 md:p-5 relative`}>
                    <button
                      onClick={() => handleDeleteClick(flip.id, flip.item_name)}
                      className="absolute top-3 right-3 text-red-500 hover:text-red-400 p-1.5 rounded hover:bg-red-500/10 transition-colors"
                      title="Delete flip permanently"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4 pr-6">
                      <div className="col-span-2 md:col-span-1">
                        <h3 className="font-bold text-base md:text-lg mb-1">
                          <button
                            className="text-luxury-gold hover:text-luxury-goldBright font-cinzel tracking-wide transition-colors text-left"
                            onClick={() => setPriceHistoryItem({ id: flip.item_id, name: flip.item_name })}
                          >
                            {flip.item_name}
                          </button>
                        </h3>
                        <p className="text-xs text-gray-400 font-outfit">
                          {formatDateTime(flip.sell_time || flip.buy_time)}
                        </p>
                      </div>

                      <div>
                        <p className="text-xs text-luxury-purpleLight/60 font-semibold uppercase tracking-wider mb-1">Quantity</p>
                        <p className="font-semibold text-sm md:text-base font-outfit">{flip.quantity_total?.toLocaleString()}</p>
                      </div>

                      <div>
                        <p className="text-xs text-luxury-purpleLight/60 font-semibold uppercase tracking-wider mb-1">Buy → Sell</p>
                        <p className="text-xs md:text-sm font-outfit">
                          <span className="text-osrs-red font-medium">{formatExactGP(flip.buy_price)}</span>
                          {' → '}
                          <span className="text-osrs-green font-medium">{formatExactGP(flip.sell_price)}</span>
                        </p>
                      </div>

                      <div>
                        <p className="text-xs text-luxury-purpleLight/60 font-semibold uppercase tracking-wider mb-1">Profit / ROI</p>
                        <p className="font-bold text-sm md:text-base font-outfit">
                          <span className={profitColor}>{formatGP(flip.profit)}</span>
                          {' / '}
                          <span className={roiColor}>{formatPercent(flip.roi)}</span>
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      ) : (
        <>
          <div className="card p-4 md:p-6 mb-4 md:mb-6">
            <h2 className="text-xl md:text-2xl font-bold font-cinzel text-transparent bg-clip-text bg-gold-gradient tracking-wide">Mutation Log</h2>
            <p className="text-sm text-luxury-purpleLight/70 font-outfit mt-1">Track all changes to your flips (trades, price updates, target adjustments)</p>
          </div>

          {(mutationsData || []).length === 0 ? (
            <div className="card text-center py-12 p-6">
              <p className="text-gray-400">No mutations recorded yet. Try updating a buy price or logging a trade!</p>
            </div>
          ) : (
            <div className="luxury-table-container">
              <table className="luxury-table">
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>Item</th>
                    <th>Action</th>
                    <th>Change</th>
                    <th>Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {(mutationsData || []).map((m) => {
                    const typeColor = 
                      m.mutation_type === 'trade' ? (m.transaction_type === 'buy' ? 'text-osrs-red' : 'text-osrs-green') :
                      m.mutation_type === 'price_update' ? 'text-luxury-purpleLight' :
                      m.mutation_type === 'adjust_target' ? 'text-amber-500' :
                      'text-gray-300';
                    
                    const actionLabel = 
                      m.mutation_type === 'trade' ? m.transaction_type.toUpperCase() :
                      m.mutation_type === 'price_update' ? 'PRICE' :
                      m.mutation_type === 'adjust_target' ? 'TARGET' :
                      m.mutation_type === 'cancel' ? 'CANCEL' : 'UPDATE';

                    return (
                      <tr key={m.id}>
                        <td className="text-xs text-gray-400 whitespace-nowrap font-outfit">
                          {formatDateTime(m.timestamp)}
                        </td>
                        <td>
                          <button
                            className="text-luxury-gold hover:text-luxury-goldBright text-sm font-semibold transition-colors text-left"
                            onClick={() => setPriceHistoryItem({ id: m.item_id, name: m.item_name })}
                          >
                            {m.item_name}
                          </button>
                        </td>
                        <td>
                          <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-md bg-luxury-darker/60 border border-luxury-border/30 ${typeColor}`}>
                            {actionLabel}
                          </span>
                        </td>
                        <td className="text-sm font-medium font-outfit">
                          {m.mutation_type === 'trade' && (
                            <span>{m.quantity?.toLocaleString()}x @ {formatExactGP(m.price)}</span>
                          )}
                          {m.mutation_type === 'price_update' && (
                            <span className="text-luxury-purpleLight">{formatExactGP(m.price)}</span>
                          )}
                          {m.mutation_type === 'adjust_target' && (
                            <span className="text-amber-500">{m.quantity?.toLocaleString()} (max)</span>
                          )}
                        </td>
                        <td className="text-xs text-gray-400 max-w-xs truncate font-outfit" title={m.notes}>
                          {m.notes}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {priceHistoryItem && (
        <PriceHistoryModal
          isOpen={!!priceHistoryItem}
          itemId={priceHistoryItem.id}
          itemName={priceHistoryItem.name}
          onClose={() => setPriceHistoryItem(null)}
        />
      )}

      <ConfirmModal
        isOpen={deleteModalOpen}
        onClose={() => {
          setDeleteModalOpen(false);
          setFlipToDelete(null);
        }}
        onConfirm={handleDeleteConfirm}
        title="Delete Flip?"
        message={`Are you sure you want to permanently delete "${flipToDelete?.name}"? This action cannot be undone and will remove all transaction history for this flip.`}
        danger={true}
      />
    </div>
  );
}