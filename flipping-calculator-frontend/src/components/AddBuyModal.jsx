import { useState } from 'react';
import { parseCash } from '../utils/formatters';

export default function AddBuyModal({ flip, onClose, onSubmit, isPending }) {
  const [quantity, setQuantity] = useState('');
  const [price, setPrice] = useState(flip.buy_price || '');
  const [notes, setNotes] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    
    const parsedQuantity = parseInt(quantity);
    const parsedPrice = parseCash(price);
    
    if (!parsedQuantity || parsedQuantity <= 0) {
      alert('Please enter a valid quantity');
      return;
    }
    
    if (!parsedPrice || parsedPrice <= 0) {
      alert('Please enter a valid price');
      return;
    }

    // Check if this would exceed intended quantity (if it exists)
    if (flip.intended_quantity) {
      const newTotal = (flip.quantity_bought || 0) + parsedQuantity;
      if (newTotal > flip.intended_quantity) {
        if (!confirm(`This will exceed your intended quantity (${flip.intended_quantity}). Continue anyway?`)) {
          return;
        }
      }
    }

    onSubmit({
      flip_id: flip.id,
      quantity: parsedQuantity,
      price: parsedPrice,
      notes: notes || undefined
    });
  };

  // Safe getters with defaults
  const quantityBought = flip.quantity_bought || 0;
  const intendedQuantity = flip.intended_quantity || 0;
  const buyPrice = flip.buy_price || 0;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-lg w-full max-w-md border border-gray-700">
        {/* Header */}
        <div className="border-b border-gray-700 p-4 flex justify-between items-center">
          <h2 className="text-xl font-bold text-white">Log Additional Buy</h2>
          <button
            className="text-gray-400 hover:text-white text-2xl"
            onClick={onClose}
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit} className="p-4">
          <div className="mb-4">
            <h3 className="text-lg font-semibold text-osrs-gold mb-2">{flip.item_name}</h3>
            <div className="text-sm text-gray-400">
              <p>Current: {quantityBought.toLocaleString()} / {intendedQuantity.toLocaleString()} bought</p>
              <p>Avg Buy Price: {buyPrice.toLocaleString()} gp</p>
            </div>
          </div>

          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium mb-1">Quantity Bought</label>
              <input
                type="number"
                className="input w-full"
                placeholder="How many did you buy?"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                autoFocus
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Buy Price (per item)</label>
              <input
                type="text"
                className="input w-full"
                placeholder="e.g. 334 or 10k or 1.5m"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                required
              />
              <p className="text-xs text-gray-400 mt-1">
                Supports K/M/B notation (e.g., 10k = 10,000)
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Notes (optional)</label>
              <input
                type="text"
                className="input w-full"
                placeholder="e.g., Morning batch"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-2 mt-6">
            <button
              type="button"
              className="btn btn-secondary flex-1"
              onClick={onClose}
              disabled={isPending}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary flex-1"
              disabled={isPending}
            >
              {isPending ? 'Logging...' : 'Log Buy'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}