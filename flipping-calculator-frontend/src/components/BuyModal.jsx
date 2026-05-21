import { useState } from 'react';
import { useBuyFlip } from '../hooks/useApi';
import { formatGP, formatExactGP } from '../utils/formatters';

export default function BuyModal({ flip, onClose }) {
  const [quantity, setQuantity] = useState(flip?.ge_limit || 1);
  const [intendedQuantity, setIntendedQuantity] = useState(flip?.ge_limit || 1);
  const [price, setPrice] = useState(flip?.buy_price || 0);
  const buyMutation = useBuyFlip();

  const totalCost = quantity * price;
  const maxQuantity = flip?.ge_limit || 999999;

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      await buyMutation.mutateAsync({
        item_name: flip.name,
        quantity: parseInt(quantity),
        price: parseInt(price),
        intended_quantity: parseInt(intendedQuantity),
        intended_sell_price: flip.sell_price, // Capture the sell price from the table
      });
      onClose();
    } catch (error) {
      console.error('Failed to log buy:', error);
    }
  };

  return (
    <div className="fixed inset-0 bg-luxury-darker/80 backdrop-blur-md flex items-center justify-center z-[70] p-2 md:p-4 animate-fade-in">
      <div className="bg-luxury-card backdrop-blur-xl rounded-2xl w-full max-w-md p-4 md:p-6 border border-luxury-purple/20 shadow-luxury-shadow shadow-purple-glow">
        <h2 className="text-lg md:text-2xl font-bold mb-4 md:mb-6 bg-gold-gradient bg-clip-text text-transparent font-cinzel">
          Buy {flip.name}
        </h2>
        
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-xs font-semibold uppercase tracking-wider text-luxury-purpleLight mb-2">Quantity Bought Now</label>
            <input
              type="number"
              className="input w-full font-mono"
              value={quantity}
              onChange={(e) => setQuantity(Math.min(parseInt(e.target.value) || 0, maxQuantity))}
              min="0"
              max={maxQuantity}
            />
            <p className="text-[10px] text-gray-400 mt-1.5 leading-relaxed">
              How many you&apos;re logging right now (0 = offer placed, nothing filled yet)
            </p>
          </div>

          <div className="mb-4">
            <label className="block text-xs font-semibold uppercase tracking-wider text-luxury-purpleLight mb-2">Intended Total Quantity</label>
            <input
              type="number"
              className="input w-full font-mono"
              value={intendedQuantity}
              onChange={(e) => setIntendedQuantity(Math.min(parseInt(e.target.value) || 0, maxQuantity))}
              min="1"
              max={maxQuantity}
              required
            />
            <p className="text-[10px] text-gray-400 mt-1.5 leading-relaxed">
              Target amount (prevents adding more than intended). Max GE Limit: {maxQuantity.toLocaleString()}
            </p>
          </div>

          <div className="mb-4">
            <label className="block text-xs font-semibold uppercase tracking-wider text-luxury-purpleLight mb-2">Price per Item</label>
            <input
              type="number"
              className="input w-full font-mono"
              value={price}
              onChange={(e) => setPrice(parseInt(e.target.value) || 0)}
              min="1"
              required
            />
            <p className="text-[10px] text-gray-400 mt-1.5 leading-relaxed">
              Suggested: <span className="text-luxury-gold font-mono">{formatExactGP(flip.buy_price)}</span>
            </p>
          </div>

          <div className="mb-6 p-4 bg-luxury-darker/40 backdrop-blur-md border border-luxury-purple/10 rounded-xl">
            <div className="flex justify-between mb-2 text-sm">
              <span className="text-luxury-purpleLight/70">Total Cost:</span>
              <span className="font-bold font-mono text-osrs-red">{formatGP(totalCost)}</span>
            </div>
            <div className="flex justify-between mb-2 text-sm">
              <span className="text-luxury-purpleLight/70">Expected Sell:</span>
              <span className="font-bold font-mono text-osrs-green">
                {formatGP(quantity * flip.sell_price)}
              </span>
            </div>
            <div className="flex justify-between border-t border-luxury-border pt-2 text-sm">
              <span className="text-luxury-purpleLight/70">Expected Profit:</span>
              <span className="font-bold font-mono text-luxury-gold">
                {formatGP(quantity * flip.profit)}
              </span>
            </div>
          </div>

          <div className="flex gap-3">
            <button
              type="submit"
              className="btn btn-primary flex-1"
              disabled={buyMutation.isPending}
            >
              {buyMutation.isPending ? 'Logging...' : 'Confirm Buy'}
            </button>
            <button
              type="button"
              className="btn btn-secondary flex-1"
              onClick={onClose}
              disabled={buyMutation.isPending}
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}