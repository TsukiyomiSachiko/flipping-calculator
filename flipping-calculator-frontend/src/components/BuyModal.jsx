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
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-[70]">
      <div className="bg-gray-800 rounded-lg p-4 md:p-6 max-w-md w-full mx-3 md:mx-4">
        <h2 className="text-lg md:text-2xl font-bold mb-3 md:mb-4 text-osrs-gold">Buy {flip.name}</h2>
        
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">Quantity Bought Now</label>
            <input
              type="number"
              className="input w-full"
              value={quantity}
              onChange={(e) => setQuantity(Math.min(parseInt(e.target.value) || 0, maxQuantity))}
              min="0"
              max={maxQuantity}
            />
            <p className="text-xs text-gray-400 mt-1">
              How many you&apos;re logging right now (0 = offer placed, nothing filled yet)
            </p>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">Intended Total Quantity</label>
            <input
              type="number"
              className="input w-full"
              value={intendedQuantity}
              onChange={(e) => setIntendedQuantity(Math.min(parseInt(e.target.value) || 0, maxQuantity))}
              min="1"
              max={maxQuantity}
              required
            />
            <p className="text-xs text-gray-400 mt-1">
              Target amount (prevents adding more than intended). Max GE Limit: {maxQuantity.toLocaleString()}
            </p>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">Price per Item</label>
            <input
              type="number"
              className="input w-full"
              value={price}
              onChange={(e) => setPrice(parseInt(e.target.value) || 0)}
              min="1"
              required
            />
            <p className="text-xs text-gray-400 mt-1">
              Suggested: {formatExactGP(flip.buy_price)}
            </p>
          </div>

          <div className="mb-6 p-4 bg-gray-700 rounded-lg">
            <div className="flex justify-between mb-2">
              <span className="text-gray-400">Total Cost:</span>
              <span className="font-bold text-osrs-red">{formatGP(totalCost)}</span>
            </div>
            <div className="flex justify-between mb-2">
              <span className="text-gray-400">Expected Sell:</span>
              <span className="font-bold text-osrs-green">
                {formatGP(quantity * flip.sell_price)}
              </span>
            </div>
            <div className="flex justify-between border-t border-gray-600 pt-2">
              <span className="text-gray-400">Expected Profit:</span>
              <span className="font-bold text-osrs-gold">
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