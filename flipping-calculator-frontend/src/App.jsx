import { useEffect, useState } from 'react';
import Navigation from './components/Navigation';
import FlipsView from './pages/FlipsView';
import LongTermFlipsView from './pages/LongTermFlipsView';
import PortfolioView from './pages/PortfolioView';
import HistoryView from './pages/HistoryView';
import StatsView from './pages/StatsView';
import HighAlchView from './pages/HighAlchView';
import LoginView from './pages/LoginView';
import ConfirmModal from './components/ConfirmModal';
import { useAppStore } from './stores/appStore';
import { useItemSync } from './hooks/useApi';
import MarketAlertMonitor from './components/MarketAlertMonitor';

function App() {
  const { activeView, currentAccount, token } = useAppStore();
  const syncMutation = useItemSync();
  const [showSyncConfirm, setShowSyncConfirm] = useState(false);
  const [syncResult, setSyncResult] = useState(null); // { type: 'success' | 'error', message: string }

  // Check if items need to be synced on first load
  useEffect(() => {
    // You can add logic here to check if items exist in the database
    // For now, we'll just make the sync button available
  }, []);

  if (!currentAccount || !token) {
    return <LoginView />;
  }

  const handleSyncClick = () => {
    setShowSyncConfirm(true);
  };

  const handleSyncConfirm = async () => {
    try {
      await syncMutation.mutateAsync();
      setSyncResult({ type: 'success', message: 'Items synced successfully!' });
      setShowSyncConfirm(false);
    } catch (error) {
      setSyncResult({ type: 'error', message: `Failed to sync items: ${error.message}` });
      setShowSyncConfirm(false);
    }
  };

  const handleSyncCancel = () => {
    setShowSyncConfirm(false);
  };

  return (
    <div className="min-h-screen bg-luxury-dark text-gray-200 font-outfit relative overflow-hidden flex flex-col justify-between">
      <MarketAlertMonitor />
      {/* Floating Luxurious Background Auroras */}
      <div className="absolute top-[-150px] left-[-150px] w-[500px] h-[500px] rounded-full bg-luxury-purple/10 blur-[130px] pointer-events-none animate-float-slow" />
      <div className="absolute bottom-[-150px] right-[-150px] w-[500px] h-[500px] rounded-full bg-luxury-gold/5 blur-[130px] pointer-events-none animate-float-delayed" />

      <div className="w-full relative z-10">
        <Navigation />
        
        <div className="container mx-auto px-3 md:px-4 pb-8">
          {/* Sync Items Button - shown on first load or in settings */}
          <div className="mb-4">
            <button
              className="btn btn-secondary text-sm flex items-center gap-2"
              onClick={handleSyncClick}
              disabled={syncMutation.isPending}
            >
              {syncMutation.isPending ? 'Syncing...' : '🔄 Sync Items from OSRS Wiki'}
            </button>
          </div>

          {/* Success/Error notification */}
          {syncResult && (
            <div className={`mb-4 p-4 rounded-xl backdrop-blur-md ${
              syncResult.type === 'success' ? 'bg-green-950/40 border border-osrs-green/30 text-green-200' : 'bg-red-955/40 border border-osrs-red/30 text-red-200'
            }`}>
              <div className="flex justify-between items-center">
                <span>
                  {syncResult.type === 'success' ? '✅' : '❌'} {syncResult.message}
                </span>
                <button
                  className="text-gray-400 hover:text-white transition-colors"
                  onClick={() => setSyncResult(null)}
                >
                  ✕
                </button>
              </div>
            </div>
          )}

          {/* Main Content */}
          {activeView === 'flips' && <FlipsView />}
          {activeView === 'longterm' && <LongTermFlipsView />}
          {activeView === 'highalch' && <HighAlchView />}
          {activeView === 'portfolio' && <PortfolioView />}
          {activeView === 'history' && <HistoryView />}
          {activeView === 'stats' && <StatsView />}
        </div>
      </div>

      {/* Sync Confirmation Modal */}
      <ConfirmModal
        isOpen={showSyncConfirm}
        title="⚠️ Sync Items from OSRS Wiki"
        message={`This will fetch ~3,000 items from the OSRS Wiki API.\n\nThis may take 1-2 minutes.\n\nContinue?`}
        onConfirm={handleSyncConfirm}
        onCancel={handleSyncCancel}
        confirmText="Sync Items"
        cancelText="Cancel"
        isLoading={syncMutation.isPending}
      />

      {/* Footer */}
      <footer className="border-t border-luxury-border/60 mt-12 py-6 relative z-10 bg-luxury-darker/60 backdrop-blur-sm">
        <div className="container mx-auto px-4 text-center text-gray-500 text-sm font-outfit">
          <p className="tracking-wide">OSRS Flipping Calculator — Track your Grand Exchange flips</p>
          <p className="mt-1 text-xs text-luxury-purple/50">Data powered by the OSRS Wiki API</p>
        </div>
      </footer>
    </div>
  );
}

export default App;