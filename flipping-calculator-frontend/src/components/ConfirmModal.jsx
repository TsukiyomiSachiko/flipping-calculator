import {} from 'react';

export default function ConfirmModal({ isOpen, title, message, onConfirm, onCancel, onClose, confirmText = 'Confirm', cancelText = 'Cancel', isLoading = false, danger = false }) {
  if (!isOpen) return null;

  const handleClose = onClose || onCancel;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4 border border-gray-700">
        <h2 className="text-xl font-bold mb-4 text-white">{title}</h2>
        
        <div className={`mb-6 whitespace-pre-line ${danger ? 'text-osrs-red' : 'text-gray-300'}`}>
          {message}
        </div>

        <div className="flex gap-3">
          <button
            className={`btn flex-1 ${danger ? 'bg-osrs-red hover:bg-red-600 text-white' : 'btn-primary'}`}
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