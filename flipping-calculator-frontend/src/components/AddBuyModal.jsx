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
    <div className="fixed inset-0 bg-luxury-darker/80 backdrop-blur-md flex items-center justify-center z-[70] p-2 md:p-4 animate-fade-in">
      <div className="bg-luxury-card backdrop-blur-xl rounded-2xl w-full max-w-md border border-luxury-purple/20 shadow-luxury-shadow shadow-purple-glow">
        {/* Header */}
        <div className="border-b border-luxury-border p-4 flex justify-between items-center">
          <h2 className="text-xl font-bold bg-gold-gradient bg-clip-text text-transparent font-cinzel">Log Additional Buy</h2>
          <button
            className="text-luxury-purpleLight hover:text-luxury-gold text-2xl transition-colors duration-200"
            onClick={onClose}
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit} className="p-4 md:p-6">
          <div className="mb-5 bg-luxury-darker/40 backdrop-blur-md border border-luxury-purple/10 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-luxury-gold mb-2 font-cinzel">{flip.item_name}</h3>
            <div className="text-xs text-luxury-purpleLight/70 font-mono space-y-1">
              <p>Current: {quantityBought.toLocaleString()} / {intendedQuantity.toLocaleString()} bought</p>
              <p>Avg Buy Price: {buyPrice.toLocaleString()} gp</p>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-luxury-purpleLight mb-2">Quantity Bought</label>
              <input
                type="number"
                className="input w-full font-mono"
                placeholder="How many did you buy?"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                autoFocus
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-luxury-purpleLight mb-2">Buy Price (per item)</label>
              <input
                type="text"
                className="input w-full font-mono"
                placeholder="e.g. 334 or 10k or 1.5m"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                required
              />
              <p className="text-[10px] text-gray-400 mt-1.5 leading-relaxed">
                Supports K/M/B notation (e.g., 10k = 10,000)
              </p>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-luxury-purpleLight mb-2">Notes (optional)</label>
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
          <div className="flex gap-3 mt-6">
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