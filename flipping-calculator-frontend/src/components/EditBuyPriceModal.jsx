import { useState, useEffect } from 'react';
import { formatGP } from '../utils/formatters';

export default function EditBuyPriceModal({ flip, isOpen, onClose, onConfirm, isPending }) {
  const [newPrice, setNewPrice] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen && flip) {
      setNewPrice(flip.buy_price.toString());
      setError('');
    }
  }, [isOpen, flip]);

  if (!isOpen || !flip) return null;

  const handleSubmit = () => {
    const price = parseInt(newPrice);
    
    if (isNaN(price) || price <= 0) {
      setError('Please enter a valid price');
      return;
    }
    
    if (price === flip.buy_price) {
      setError('New price must be different from current price');
      return;
    }
    
    onConfirm(price);
  };

  const priceDiff = parseInt(newPrice) - flip.buy_price;
  const quantityBought = flip.quantity_total;
  const intendedQty = flip.intended_quantity || 0;
  const unfilledQty = intendedQty > quantityBought ? intendedQty - quantityBought : 0;
  
  // Calculate cash adjustment
  let cashAdjustment = 0;
  if (quantityBought > 0) {
    cashAdjustment += priceDiff * quantityBought;
  }
  if (unfilledQty > 0) {
    cashAdjustment += priceDiff * unfilledQty;
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="card max-w-md w-full">
        <h3 className="text-xl font-bold mb-4">Edit Buy Price</h3>
        
        <div className="space-y-4">
          <div>
            <p className="text-sm text-gray-400 mb-2">
              {flip.item_name}
            </p>
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Current Price:</span>
              <span className="font-bold">{formatGP(flip.buy_price)}</span>
            </div>
            {quantityBought > 0 && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Quantity Bought:</span>
                <span>{quantityBought.toLocaleString()}</span>
              </div>
            )}
            {intendedQty > 0 && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Intended Quantity:</span>
                <span>{intendedQty.toLocaleString()}</span>
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">New Buy Price</label>
            <input
              type="number"
              className="input w-full"
              value={newPrice}
              onChange={(e) => {
                setNewPrice(e.target.value);
                setError('');
              }}
              placeholder="Enter new price"
              autoFocus
            />
            {error && <p className="text-red-400 text-sm mt-1">{error}</p>}
          </div>

          {!isNaN(parseInt(newPrice)) && parseInt(newPrice) !== flip.buy_price && (
            <div className="bg-gray-700 p-3 rounded space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Price Change:</span>
                <span className={priceDiff > 0 ? 'text-osrs-red' : 'text-osrs-green'}>
                  {priceDiff > 0 ? '+' : ''}{formatGP(priceDiff)}
                </span>
              </div>
              {cashAdjustment !== 0 && (
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Cash Adjustment:</span>
                  <span className={cashAdjustment > 0 ? 'text-osrs-red' : 'text-osrs-green'}>
                    {cashAdjustment > 0 ? '-' : '+'}{formatGP(Math.abs(cashAdjustment))}
                  </span>
                </div>
              )}
              <p className="text-xs text-gray-400 mt-2">
                {cashAdjustment > 0 
                  ? `You'll need ${formatGP(cashAdjustment)} more cash` 
                  : cashAdjustment < 0
                  ? `You'll get ${formatGP(Math.abs(cashAdjustment))} cash back`
                  : 'No cash adjustment needed'}
              </p>
            </div>
          )}

          <div className="flex gap-2">
            <button
              className="btn btn-secondary flex-1"
              onClick={onClose}
              disabled={isPending}
            >
              Cancel
            </button>
            <button
              className="btn btn-primary flex-1"
              onClick={handleSubmit}
              disabled={isPending}
            >
              {isPending ? 'Updating...' : 'Update Price'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
