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
    <div className="fixed inset-0 bg-luxury-darker/80 backdrop-blur-md flex items-center justify-center z-[70] p-2 md:p-4 animate-fade-in">
      <div className="bg-luxury-card backdrop-blur-xl rounded-2xl w-full max-w-md p-4 md:p-6 border border-luxury-purple/20 shadow-luxury-shadow shadow-purple-glow">
        <h3 className="text-xl font-bold mb-4 bg-gold-gradient bg-clip-text text-transparent font-cinzel">Edit Buy Price</h3>
        
        <div className="space-y-4">
          <div className="bg-luxury-darker/40 backdrop-blur-md border border-luxury-purple/10 rounded-xl p-4">
            <p className="text-sm font-semibold text-luxury-gold mb-2 font-cinzel">
              {flip.item_name}
            </p>
            <div className="flex justify-between text-xs font-mono text-luxury-purpleLight/70">
              <span>Current Price:</span>
              <span className="font-bold text-white">{formatGP(flip.buy_price)}</span>
            </div>
            {quantityBought > 0 && (
              <div className="flex justify-between text-xs font-mono text-luxury-purpleLight/70 mt-1">
                <span>Quantity Bought:</span>
                <span className="text-white">{quantityBought.toLocaleString()}</span>
              </div>
            )}
            {intendedQty > 0 && (
              <div className="flex justify-between text-xs font-mono text-luxury-purpleLight/70 mt-1">
                <span>Intended Quantity:</span>
                <span className="text-white">{intendedQty.toLocaleString()}</span>
              </div>
            )}
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-luxury-purpleLight mb-2">New Buy Price</label>
            <input
              type="number"
              className="input w-full font-mono"
              value={newPrice}
              onChange={(e) => {
                setNewPrice(e.target.value);
                setError('');
              }}
              placeholder="Enter new price"
              autoFocus
            />
            {error && <p className="text-osrs-red text-xs mt-1.5 font-medium">{error}</p>}
          </div>

          {!isNaN(parseInt(newPrice)) && parseInt(newPrice) !== flip.buy_price && (
            <div className="bg-luxury-darker/40 backdrop-blur-md border border-luxury-purple/10 p-4 rounded-xl space-y-2 text-xs font-mono">
              <div className="flex justify-between">
                <span className="text-luxury-purpleLight/70">Price Change:</span>
                <span className={priceDiff > 0 ? 'text-osrs-red' : 'text-osrs-green'}>
                  {priceDiff > 0 ? '+' : ''}{formatGP(priceDiff)}
                </span>
              </div>
              {cashAdjustment !== 0 && (
                <div className="flex justify-between">
                  <span className="text-luxury-purpleLight/70">Cash Adjustment:</span>
                  <span className={cashAdjustment > 0 ? 'text-osrs-red' : 'text-osrs-green'}>
                    {cashAdjustment > 0 ? '-' : '+'}{formatGP(Math.abs(cashAdjustment))}
                  </span>
                </div>
              )}
              <p className="text-[10px] text-gray-400 mt-2 font-sans leading-relaxed">
                {cashAdjustment > 0 
                  ? `You'll need ${formatGP(cashAdjustment)} more cash` 
                  : cashAdjustment < 0
                  ? `You'll get ${formatGP(Math.abs(cashAdjustment))} cash back`
                  : 'No cash adjustment needed'}
              </p>
            </div>
          )}

          <div className="flex gap-3">
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
