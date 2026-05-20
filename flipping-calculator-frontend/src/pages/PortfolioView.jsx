import { useState } from 'react';
import { usePendingProjections, useSellFlip, useAddBuy, useCancelFlip, useAdjustIntended, useUpdateBuyPrice } from '../hooks/useApi';
import { portfolioApi } from '../services/api';
import { useQueryClient } from '@tanstack/react-query';
import PortfolioSummary from '../components/PortfolioSummary';
import PriceHistoryModal from '../components/PriceHistoryModal';
import RecoveryPanel from '../components/RecoveryPanel';
import ConfirmModal from '../components/ConfirmModal';
import AddBuyModal from '../components/AddBuyModal';
import EditBuyPriceModal from '../components/EditBuyPriceModal';
import Toast from '../components/Toast';
import { formatGP, formatExactGP, formatDateTime, formatPercent } from '../utils/formatters';

export default function PortfolioView() {
  const queryClient = useQueryClient();
  const { data: projectionData, isLoading } = usePendingProjections();
  const sellMutation = useSellFlip();
  const addBuyMutation = useAddBuy();
  const cancelMutation = useCancelFlip();
  const adjustIntendedMutation = useAdjustIntended();
  const updateBuyPriceMutation = useUpdateBuyPrice();

  const [sellForm, setSellForm] = useState({});
  const [priceMode, setPriceMode] = useState({}); // Track per-item vs total mode for each flip
  const [priceHistoryItem, setPriceHistoryItem] = useState(null);
  const [showRecovery, setShowRecovery] = useState({}); // Track which flips show recovery analysis
  const [cancelModalOpen, setCancelModalOpen] = useState(false);
  const [flipToCancel, setFlipToCancel] = useState(null);
  const [addBuyModalOpen, setAddBuyModalOpen] = useState(false);
  const [flipToAddBuy, setFlipToAddBuy] = useState(null);
  const [adjustIntendedModalOpen, setAdjustIntendedModalOpen] = useState(false);
  const [flipToAdjustIntended, setFlipToAdjustIntended] = useState(null);
  const [editBuyPriceModalOpen, setEditBuyPriceModalOpen] = useState(false);
  const [flipToEditPrice, setFlipToEditPrice] = useState(null);
  const [toast, setToast] = useState(null); // { message, type }

  const handleExport = async () => {
    try {
      setToast({ message: 'Starting export...', type: 'info' });
      const response = await portfolioApi.export();
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      const dateStr = new Date().toISOString().split('T')[0];
      link.setAttribute('download', `portfolio_export_${dateStr}.csv`);
      document.body.appendChild(link);
      link.click();
      
      // Cleanup
      link.remove();
      window.URL.revokeObjectURL(url);
      setToast({ message: 'Portfolio exported successfully', type: 'success' });
    } catch (error) {
      console.error('Export failed:', error);
      setToast({ message: 'Export failed', type: 'error' });
    }
  };

  const handleImport = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Reset input value to allow re-uploading same file if needed
    event.target.value = '';

    try {
      setToast({ message: 'Importing data...', type: 'info' });
      const response = await portfolioApi.import(file);
      const stats = response.data;
      
      if (stats.errors > 0) {
        console.warn('Import completed with errors:', stats.details);
      }
      
      setToast({ 
        message: `Imported: ${stats.imported}, Skipped: ${stats.skipped}, Errors: ${stats.errors}`, 
        type: stats.errors > 0 ? 'warning' : 'success' 
      });
      
      // Refresh data
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
      // Also invalidate flips search results as liquidity/volume data might be cached but portfolio state affects UI
      queryClient.invalidateQueries({ queryKey: ['flips'] });
      
    } catch (error) {
      console.error('Import failed:', error);
      setToast({ message: 'Import failed: ' + (error.message || 'Unknown error'), type: 'error' });
    }
  };

  const handleSell = async (flipId) => {
    const form = sellForm[flipId];
    const mode = priceMode[flipId] || 'total'; // Changed default to 'total'
    
    if (!form?.price) {
      alert(mode === 'total' ? 'Please enter total price' : 'Please enter a sell price');
      return;
    }
    
    if (mode === 'total' && !form?.quantity) {
      alert('Quantity is required when using total price');
      return;
    }

    try {
      const payload = {
        flip_id: flipId,
        quantity: form.quantity ? parseInt(form.quantity) : undefined,
      };
      
      // Add either price or price_total based on mode
      if (mode === 'total') {
        payload.price_total = parseInt(form.price);
      } else {
        payload.price = parseInt(form.price);
      }
      
      await sellMutation.mutateAsync(payload);
      setSellForm({ ...sellForm, [flipId]: {} });
    } catch (error) {
      console.error('Failed to sell:', error);
    }
  };

  const handleSellAtMarket = async (flip) => {
    if (!flip.current_sell_price) return;
    if (!confirm(`Sell ${flip.quantity_remaining.toLocaleString()}x ${flip.item_name} at ${flip.current_sell_price.toLocaleString()} gp each?`)) return;

    try {
      await sellMutation.mutateAsync({
        flip_id: flip.id,
        price: flip.current_sell_price,
        quantity: flip.quantity_remaining,
      });
    } catch (error) {
      console.error('Failed to sell at market:', error);
    }
  };

  const handleCancelClick = (flip) => {
    setFlipToCancel(flip);
    setCancelModalOpen(true);
  };

  const handleCancelConfirm = async () => {
    if (!flipToCancel) return;
    
    try {
      await cancelMutation.mutateAsync(flipToCancel.id);
      setCancelModalOpen(false);
      setFlipToCancel(null);
    } catch (error) {
      console.error('Failed to cancel:', error);
    }
  };

  const handleAddBuyClick = (flip) => {
    setFlipToAddBuy(flip);
    setAddBuyModalOpen(true);
  };

  const handleAddBuySubmit = async (data) => {
    try {
      await addBuyMutation.mutateAsync(data);
      setAddBuyModalOpen(false);
      setFlipToAddBuy(null);
    } catch (error) {
      console.error('Failed to add buy:', error);
      alert(`Failed to log buy: ${error.message}`);
    }
  };

  const handleAdjustIntended = async (flipId) => {
    try {
      const response = await adjustIntendedMutation.mutateAsync(flipId);
      console.log('Adjust intended response:', response);
      
      // Axios wraps response in .data
      const data = response.data || response;
      const message = data.message || 'Intended quantity adjusted successfully';
      
      // Close modal and clear state
      setAdjustIntendedModalOpen(false);
      setFlipToAdjustIntended(null);
      
      // Show success toast
      setToast({ message, type: 'success' });
    } catch (error) {
      console.error('Failed to adjust intended quantity:', error);
      
      // Extract error message from various possible locations
      let errorMsg = 'Unknown error';
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        errorMsg = detail.error || detail;
      } else if (error.message) {
        errorMsg = error.message;
      }
      
      // Show error toast
      setToast({ message: `Failed to adjust: ${errorMsg}`, type: 'error' });
    }
  };

  const handleUpdateBuyPrice = async (newPrice) => {
    try {
      const response = await updateBuyPriceMutation.mutateAsync({
        flipId: flipToEditPrice.id,
        newPrice
      });
      console.log('Update buy price response:', response);
      
      // Axios wraps response in .data
      const data = response.data || response;
      const message = data.message || 'Buy price updated successfully';
      
      // Close modal and clear state
      setEditBuyPriceModalOpen(false);
      setFlipToEditPrice(null);
      
      // Show success toast
      setToast({ message, type: 'success' });
    } catch (error) {
      console.error('Failed to update buy price:', error);
      
      // Extract error message from various possible locations
      let errorMsg = 'Unknown error';
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        errorMsg = detail.error || detail;
      } else if (error.message) {
        errorMsg = error.message;
      }
      
      // Show error toast
      setToast({ message: `Failed to update price: ${errorMsg}`, type: 'error' });
    }
  };

  const updateSellForm = (flipId, field, value) => {
    setSellForm({
      ...sellForm,
      [flipId]: {
        ...sellForm[flipId],
        [field]: value,
      },
    });
  };

  if (isLoading) {
    return (
      <div>
        <PortfolioSummary />
        <div className="card text-center py-12">
          <p className="text-gray-400">Loading portfolio...</p>
        </div>
      </div>
    );
  }

  const flips = projectionData?.flips || [];
  const totalProjectedProfit = projectionData?.total_projected_profit || 0;
  const totalCurrentValue = projectionData?.total_current_value || 0;

  return (
    <div>
      <PortfolioSummary
        projectedProfit={totalProjectedProfit}
        currentValue={totalCurrentValue}
      />

      <div className="card">
        <div className="flex justify-between items-center mb-3 md:mb-4">
          <h2 className="text-lg md:text-2xl font-bold text-osrs-gold">Pending Flips</h2>
          <div className="flex gap-2">
            <button 
              onClick={handleExport}
              className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm text-gray-300 border border-gray-600 transition-colors flex items-center gap-1"
              title="Export all flips to CSV"
            >
              ⬇️ <span className="hidden sm:inline">Export</span>
            </button>
            <label 
              className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm text-gray-300 border border-gray-600 transition-colors cursor-pointer flex items-center gap-1"
              title="Import flips from CSV"
            >
              ⬆️ <span className="hidden sm:inline">Import</span>
              <input type="file" accept=".csv" className="hidden" onChange={handleImport} />
            </label>
          </div>
        </div>
        
        {flips.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-400">No pending flips. Start by finding some profitable items!</p>
          </div>
        ) : (
          <div className="space-y-4">
            {flips.map((flip) => {
              const soldQuantity = flip.quantity_total - flip.quantity_remaining;
              const hasPartialSale = soldQuantity > 0;
              const hasProjection = flip.projected_profit != null;
              const projectedPositive = flip.projected_profit_remaining > 0;
              
              return (
                <div key={flip.id} className="bg-gray-700 rounded-lg p-3 md:p-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <h3 className="text-base md:text-xl font-bold mb-2">
                        <button
                          className="text-osrs-gold hover:text-yellow-300 transition-colors"
                          onClick={() => setPriceHistoryItem({ id: flip.item_id, name: flip.item_name })}
                        >
                          {flip.item_name}
                        </button>
                      </h3>
                      <div className="space-y-1 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-400 flex items-center gap-1">
                            Quantity:
                            <span 
                              className="cursor-help text-xs border border-gray-500 rounded-full w-4 h-4 flex items-center justify-center"
                              title="Current owned / Total bought / Intended target"
                            >
                              ?
                            </span>
                          </span>
                          <span className="font-medium">
                            {flip.quantity_remaining?.toLocaleString()}
                            {hasPartialSale && (
                              <span className="text-gray-500 ml-1">
                                / {flip.quantity_total?.toLocaleString()}
                              </span>
                            )}
                            {flip.intended_quantity && (
                              <span className="text-gray-600 ml-1">
                                / {flip.intended_quantity?.toLocaleString()}
                              </span>
                            )}
                          </span>
                        </div>
                        {hasPartialSale && (
                          <div className="flex justify-between">
                            <span className="text-gray-400">Already Sold:</span>
                            <span className="text-osrs-green">
                              {soldQuantity.toLocaleString()}
                              {flip.sell_price && (
                                <span className="text-gray-400"> @ {formatExactGP(flip.sell_price)}</span>
                              )}
                            </span>
                          </div>
                        )}
                        <div className="flex justify-between items-center">
                          <span className="text-gray-400">Buy Price:</span>
                          <div className="flex items-center gap-2">
                            <span className="text-osrs-red">{formatExactGP(flip.buy_price)}</span>
                            <button
                              className="text-xs text-osrs-blue hover:text-blue-400 transition-colors px-2 py-0.5 rounded border border-osrs-blue hover:border-blue-400"
                              onClick={() => {
                                setFlipToEditPrice(flip);
                                setEditBuyPriceModalOpen(true);
                              }}
                              title="Edit buy price"
                            >
                              ✏️
                            </button>
                          </div>
                        </div>
                        {flip.break_even_price && (
                          <div className="flex justify-between">
                            <span className="text-gray-400">Break-Even Price:</span>
                            <span className="text-yellow-400 font-medium">{formatExactGP(flip.break_even_price)}</span>
                          </div>
                        )}
                        {flip.intended_sell_price && (
                          <div className="flex justify-between">
                            <span className="text-gray-400">Target Sell Price:</span>
                            <span className="text-osrs-green">{formatExactGP(flip.intended_sell_price)}</span>
                          </div>
                        )}
                        <div className="flex justify-between">
                          <span className="text-gray-400">Total Invested:</span>
                          <span className="text-osrs-red font-bold">{formatGP(flip.buy_price * flip.quantity_total)}</span>
                        </div>
                        {hasPartialSale && flip.profit && (
                          <>
                            <div className="flex justify-between">
                              <span className="text-gray-400">Profit So Far:</span>
                              <span className="text-osrs-green font-bold">{formatGP(flip.profit)}</span>
                            </div>
                            {flip.realized_roi != null && (
                              <div className="flex justify-between">
                                <span className="text-gray-400">Realized ROI:</span>
                                <span className={`font-bold ${flip.realized_roi > 0 ? 'text-osrs-green' : 'text-osrs-red'}`}>
                                  {formatPercent(flip.realized_roi)}
                                </span>
                              </div>
                            )}
                          </>
                        )}
                        <div className="flex justify-between">
                          <span className="text-gray-400">Created:</span>
                          <span>{formatDateTime(flip.buy_time)}</span>
                        </div>

                        {/* Fill Rate Monitoring - Buy Status */}
                        {flip.fill_metrics?.buy_metrics && (
                          <div className="border-t border-gray-600 mt-2 pt-2">
                            <div className="flex justify-between items-center mb-1">
                              <span className="text-gray-400">Buy Status:</span>
                              <span className={`text-xs px-2 py-1 rounded font-medium ${
                                flip.fill_metrics.buy_metrics.badge_color === 'green' ? 'bg-green-900 text-green-300' :
                                flip.fill_metrics.buy_metrics.badge_color === 'yellow' ? 'bg-yellow-900 text-yellow-300' :
                                'bg-red-900 text-red-300'
                              }`}>
                                {flip.fill_metrics.buy_metrics.recommendation_text}
                              </span>
                            </div>
                            <div className="flex justify-between text-xs text-gray-500">
                              <span>Fill rate:</span>
                              <span className="text-gray-300">
                                {Math.round(flip.fill_metrics.buy_metrics.actual_fill_rate)}/hr
                                {flip.fill_metrics.buy_metrics.expected_fill_rate > 0 && 
                                  <span className="text-gray-500"> (exp: {Math.round(flip.fill_metrics.buy_metrics.expected_fill_rate)}/hr)</span>
                                }
                              </span>
                            </div>
                            <div className="flex justify-between text-xs text-gray-500">
                              <span>Last buy:</span>
                              <span className="text-gray-300">
                                {flip.fill_metrics.buy_metrics.hours_since_last_buy < 1 
                                  ? `${Math.round(flip.fill_metrics.buy_metrics.hours_since_last_buy * 60)}m ago`
                                  : `${flip.fill_metrics.buy_metrics.hours_since_last_buy.toFixed(1)}h ago`
                                }
                              </span>
                            </div>
                            <div className="flex justify-between text-xs text-gray-500">
                              <span>Progress:</span>
                              <span className="text-gray-300">
                                {flip.fill_metrics.buy_metrics.fill_progress.toFixed(0)}% filled
                              </span>
                            </div>
                          </div>
                        )}

                        {/* Fill Rate Monitoring - Sell Status */}
                        {flip.fill_metrics?.sell_metrics && (
                          <div className="border-t border-gray-600 mt-2 pt-2">
                            <div className="flex justify-between items-center mb-1">
                              <span className="text-gray-400">Sell Status:</span>
                              <span className={`text-xs px-2 py-1 rounded font-medium ${
                                flip.fill_metrics.sell_metrics.badge_color === 'green' ? 'bg-green-900 text-green-300' :
                                flip.fill_metrics.sell_metrics.badge_color === 'yellow' ? 'bg-yellow-900 text-yellow-300' :
                                'bg-red-900 text-red-300'
                              }`}>
                                {flip.fill_metrics.sell_metrics.recommendation_text}
                              </span>
                            </div>
                            <div className="flex justify-between text-xs text-gray-500">
                              <span>Sell rate:</span>
                              <span className="text-gray-300">
                                {Math.round(flip.fill_metrics.sell_metrics.actual_sell_rate)}/hr
                                {flip.fill_metrics.sell_metrics.expected_sell_rate > 0 && 
                                  <span className="text-gray-500"> (exp: {Math.round(flip.fill_metrics.sell_metrics.expected_sell_rate)}/hr)</span>
                                }
                              </span>
                            </div>
                            <div className="flex justify-between text-xs text-gray-500">
                              <span>Last sell:</span>
                              <span className="text-gray-300">
                                {flip.fill_metrics.sell_metrics.hours_since_last_sell < 1 
                                  ? `${Math.round(flip.fill_metrics.sell_metrics.hours_since_last_sell * 60)}m ago`
                                  : `${flip.fill_metrics.sell_metrics.hours_since_last_sell.toFixed(1)}h ago`
                                }
                              </span>
                            </div>
                            <div className="flex justify-between text-xs text-gray-500">
                              <span>In inventory:</span>
                              <span className="text-gray-300">
                                {flip.fill_metrics.sell_metrics.time_in_inventory_hours < 1 
                                  ? `${Math.round(flip.fill_metrics.sell_metrics.time_in_inventory_hours * 60)}m`
                                  : `${flip.fill_metrics.sell_metrics.time_in_inventory_hours.toFixed(1)}h`
                                }
                              </span>
                            </div>
                          </div>
                        )}

                        {/* Projection section */}
                        {hasProjection && (
                          <>
                            <div className="border-t border-gray-600 mt-2 pt-2">
                              <div className="flex justify-between">
                                <span className="text-gray-400">Current Market Price:</span>
                                <span className="text-osrs-blue font-medium">{formatExactGP(flip.current_sell_price)}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-400">If Sold Now (remaining):</span>
                                <span className={`font-bold ${projectedPositive ? 'text-osrs-green' : 'text-osrs-red'}`}>
                                  {formatGP(flip.projected_profit_remaining)}
                                </span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-400">Total Projected Profit:</span>
                                <span className={`font-bold ${flip.projected_profit > 0 ? 'text-osrs-green' : 'text-osrs-red'}`}>
                                  {formatGP(flip.projected_profit)}
                                </span>
                              </div>
                              {flip.projected_roi != null && (
                                <div className="flex justify-between">
                                  <span className="text-gray-400">Projected ROI:</span>
                                  <span className={`font-bold ${flip.projected_roi > 0 ? 'text-osrs-green' : 'text-osrs-red'}`}>
                                    {formatPercent(flip.projected_roi)}
                                  </span>
                                </div>
                              )}
                            </div>
                          </>
                        )}
                        {!hasProjection && (
                          <div className="border-t border-gray-600 mt-2 pt-2">
                            <span className="text-gray-500 text-xs">No live price data available</span>
                          </div>
                        )}

                        {/* Recovery Analysis Toggle */}
                        <div className="mt-2">
                          <button
                            className={`text-xs px-3 py-1 rounded transition-colors ${
                              showRecovery[flip.id]
                                ? 'bg-osrs-blue text-white'
                                : 'bg-gray-600 text-gray-300 hover:bg-gray-500'
                            }`}
                            onClick={() => setShowRecovery(prev => ({ ...prev, [flip.id]: !prev[flip.id] }))}
                          >
                            🔮 {showRecovery[flip.id] ? 'Hide' : 'Show'} Recovery Analysis
                          </button>
                        </div>

                        {showRecovery[flip.id] && (
                          <RecoveryPanel flipId={flip.id} />
                        )}
                      </div>
                    </div>

                    <div>
                      <h4 className="font-semibold mb-2">Log Additional Purchase</h4>
                      
                      {/* Only show Log Buy if haven't reached intended quantity yet */}
                      {(!flip.intended_quantity || flip.quantity_total < flip.intended_quantity) && (
                        <button
                          className="btn bg-osrs-gold hover:bg-yellow-500 text-black w-full mb-4"
                          onClick={() => handleAddBuyClick(flip)}
                          disabled={addBuyMutation.isPending}
                        >
                          📦 Log Buy
                        </button>
                      )}

                      {flip.intended_quantity && flip.quantity_total >= flip.intended_quantity && (
                        <div className="mb-4 p-3 bg-green-900/30 border border-green-700 rounded text-sm text-green-300">
                          ✓ Target reached ({flip.quantity_total.toLocaleString()} / {flip.intended_quantity.toLocaleString()})
                        </div>
                      )}

                      {flip.intended_quantity && flip.intended_quantity > flip.quantity_total && (
                        <div className="mb-4">
                          <button
                            className="btn bg-orange-600 hover:bg-orange-700 text-white w-full text-sm"
                            onClick={() => {
                              setFlipToAdjustIntended(flip);
                              setAdjustIntendedModalOpen(true);
                            }}
                            disabled={adjustIntendedMutation.isPending}
                            title="Set intended quantity to current quantity and free up reserved cash"
                          >
                            💰 Adjust Target ({flip.quantity_total.toLocaleString()} / {flip.intended_quantity.toLocaleString()})
                          </button>
                          <p className="text-xs text-gray-400 mt-1 text-center">
                            Free up {formatGP((flip.intended_quantity - flip.quantity_total) * flip.buy_price)} reserved cash
                          </p>
                        </div>
                      )}

                      <h4 className="font-semibold mb-2">Sell This Flip</h4>
                      <div className="space-y-2">
                        {/* Price Mode Toggle */}
                        <div className="flex gap-1 md:gap-2 mb-3">
                          <button
                            className={`flex-1 px-2 md:px-3 py-1 rounded text-xs md:text-sm transition-colors ${
                              priceMode[flip.id] === 'per_item'
                                ? 'bg-osrs-gold text-black'
                                : 'bg-gray-600 text-gray-300 hover:bg-gray-500'
                            }`}
                            onClick={() => setPriceMode({ ...priceMode, [flip.id]: 'per_item' })}
                          >
                            Per Item
                          </button>
                          <button
                            className={`flex-1 px-2 md:px-3 py-1 rounded text-xs md:text-sm transition-colors ${
                              (priceMode[flip.id] || 'total') === 'total'
                                ? 'bg-osrs-gold text-black'
                                : 'bg-gray-600 text-gray-300 hover:bg-gray-500'
                            }`}
                            onClick={() => setPriceMode({ ...priceMode, [flip.id]: 'total' })}
                          >
                            Total Price
                          </button>
                        </div>
                        
                        <div>
                          <label className="block text-xs text-gray-400 mb-1">
                            {(priceMode[flip.id] || 'total') === 'total' ? 'Total Sale Price (before tax)' : 'Price Per Item'}
                          </label>
                          <input
                            type="number"
                            className="input w-full"
                            placeholder={(priceMode[flip.id] || 'total') === 'total' ? 'Total amount received' : 'Price per item'}
                            value={sellForm[flip.id]?.price || ''}
                            onChange={(e) => updateSellForm(flip.id, 'price', e.target.value)}
                          />
                          {(priceMode[flip.id] || 'total') === 'total' && sellForm[flip.id]?.price && sellForm[flip.id]?.quantity && (
                            <p className="text-xs text-gray-400 mt-1">
                              ≈ {Math.floor(parseInt(sellForm[flip.id].price) / parseInt(sellForm[flip.id].quantity)).toLocaleString()} gp per item
                            </p>
                          )}
                        </div>
                        <div>
                          <label className="block text-xs text-gray-400 mb-1">
                            Quantity {(priceMode[flip.id] || 'total') === 'total' ? '(required)' : '(leave empty for full sale)'}
                          </label>
                          <input
                            type="number"
                            className="input w-full"
                            placeholder={`Max: ${flip.quantity_remaining}`}
                            max={flip.quantity_remaining}
                            value={sellForm[flip.id]?.quantity || ''}
                            onChange={(e) => updateSellForm(flip.id, 'quantity', e.target.value)}
                          />
                        </div>
                        <div className="flex flex-wrap gap-2 mt-3">
                          <button
                            className="btn btn-primary flex-1 min-w-0"
                            onClick={() => handleSell(flip.id)}
                            disabled={sellMutation.isPending}
                          >
                            Sell
                          </button>
                          {flip.current_sell_price && (
                            <button
                              className="btn bg-osrs-blue hover:bg-blue-600 text-white flex-1 min-w-0 text-xs md:text-sm"
                              onClick={() => handleSellAtMarket(flip)}
                              disabled={sellMutation.isPending}
                            >
                              Sell @ {formatExactGP(flip.current_sell_price)}
                            </button>
                          )}
                          <button
                            className="btn btn-secondary min-w-0"
                            onClick={() => handleCancelClick(flip)}
                            disabled={cancelMutation.isPending}
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {priceHistoryItem && (
        <PriceHistoryModal
          isOpen={!!priceHistoryItem}
          itemId={priceHistoryItem.id}
          itemName={priceHistoryItem.name}
          onClose={() => setPriceHistoryItem(null)}
        />
      )}

      <ConfirmModal
        isOpen={cancelModalOpen}
        onClose={() => {
          setCancelModalOpen(false);
          setFlipToCancel(null);
        }}
        onConfirm={handleCancelConfirm}
        title="Cancel Flip?"
        message={
          flipToCancel?.quantity_remaining > 0
            ? `⚠️ Warning: You still have ${flipToCancel.quantity_remaining.toLocaleString()} ${flipToCancel.item_name} in your inventory!\n\nCancelling now means you're holding items at risk. Consider selling them first to lock in profit/loss.\n\nThe flip will be marked as cancelled but data will be preserved for your records.`
            : `Are you sure you want to cancel the flip for "${flipToCancel?.item_name}"? The flip will be marked as cancelled but data will be preserved for your records.`
        }
        danger={flipToCancel?.quantity_remaining > 0}
      />

      {addBuyModalOpen && flipToAddBuy && (
        <AddBuyModal
          flip={flipToAddBuy}
          onClose={() => {
            setAddBuyModalOpen(false);
            setFlipToAddBuy(null);
          }}
          onSubmit={handleAddBuySubmit}
          isPending={addBuyMutation.isPending}
        />
      )}

      <ConfirmModal
        isOpen={adjustIntendedModalOpen}
        onClose={() => {
          setAdjustIntendedModalOpen(false);
          setFlipToAdjustIntended(null);
        }}
        onConfirm={() => handleAdjustIntended(flipToAdjustIntended.id)}
        title="Adjust Intended Quantity?"
        message={
          flipToAdjustIntended
            ? `Are you sure you want to adjust the intended quantity for "${flipToAdjustIntended.item_name}"?\n\nThis will:\n• Set intended quantity from ${flipToAdjustIntended.intended_quantity?.toLocaleString()} to ${flipToAdjustIntended.quantity_total?.toLocaleString()}\n• Free up ${formatGP((flipToAdjustIntended.intended_quantity - flipToAdjustIntended.quantity_total) * flipToAdjustIntended.buy_price)} reserved cash\n\nThis action cannot be undone.`
            : ''
        }
        danger={false}
      />

      <EditBuyPriceModal
        flip={flipToEditPrice}
        isOpen={editBuyPriceModalOpen}
        onClose={() => {
          setEditBuyPriceModalOpen(false);
          setFlipToEditPrice(null);
        }}
        onConfirm={handleUpdateBuyPrice}
        isPending={updateBuyPriceMutation.isPending}
      />

      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
}