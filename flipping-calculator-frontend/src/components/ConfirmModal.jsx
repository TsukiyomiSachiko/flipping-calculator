import {} from 'react';

export default function ConfirmModal({ isOpen, title, message, onConfirm, onCancel, onClose, confirmText = 'Confirm', cancelText = 'Cancel', isLoading = false, danger = false }) {
  if (!isOpen) return null;

  const handleClose = onClose || onCancel;

  return (
    <div className="fixed inset-0 bg-luxury-darker/80 backdrop-blur-md flex items-center justify-center z-[70] p-2 md:p-4 animate-fade-in">
      <div className="bg-luxury-card backdrop-blur-xl rounded-2xl w-full max-w-md p-6 border border-luxury-purple/20 shadow-luxury-shadow shadow-purple-glow">
        <h2 className="text-xl font-bold mb-4 bg-gold-gradient bg-clip-text text-transparent font-cinzel">{title}</h2>
        
        <div className={`mb-6 text-sm whitespace-pre-line leading-relaxed ${danger ? 'text-osrs-red font-semibold' : 'text-luxury-purpleLight'}`}>
          {message}
        </div>

        <div className="flex gap-3">
          <button
            className={`btn flex-1 ${danger ? 'bg-gradient-to-r from-red-800 to-osrs-red text-white border border-red-500/20 hover:from-red-700 hover:to-red-500 shadow-[0_4px_15px_rgba(244,63,94,0.15)] hover:shadow-[0_6px_20px_rgba(244,63,94,0.25)]' : 'btn-primary'}`}
            onClick={onConfirm}
            disabled={isLoading}
          >
            {isLoading ? 'Loading...' : confirmText}
          </button>
          <button
            className="btn btn-secondary flex-1"
            onClick={handleClose}
            disabled={isLoading}
          >
            {cancelText}
          </button>
        </div>
      </div>
    </div>
  );
}