import { useEffect, useState, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAppStore } from '../stores/appStore';
import { portfolioApi } from '../services/api';
import { formatGP } from '../utils/formatters';
import { playAlertSound } from '../utils/sound';

let flashInterval = null;

const startTabFlashing = (message) => {
  if (flashInterval) return;
  const originalTitle = "OSRS Flipping Calculator";
  let showMessage = true;
  flashInterval = setInterval(() => {
    document.title = showMessage ? message : originalTitle;
    showMessage = !showMessage;
  }, 1000);
};

const stopTabFlashing = () => {
  if (flashInterval) {
    clearInterval(flashInterval);
    flashInterval = null;
  }
  document.title = "OSRS Flipping Calculator";
};

export default function MarketAlertMonitor() {
  const { alertSettings, currentAccount, setActiveView } = useAppStore();
  const accountId = currentAccount?.id || 0;
  
  // Track active alerts to show in the in-app modal
  const [activeAlerts, setActiveAlerts] = useState([]);
  const [showModal, setShowModal] = useState(false);
  
  // Track already-alerted flips in the session to avoid spamming the user
  // Map key: flipId -> value: lastAlertedPrice
  const alertedFlipsRef = useRef(null);
  if (alertedFlipsRef.current === null) {
    try {
      const stored = localStorage.getItem('flipping_calculator_alerted_flips');
      alertedFlipsRef.current = stored ? new Map(JSON.parse(stored)) : new Map();
    } catch (e) {
      console.error('Failed to parse alerted flips from localStorage:', e);
      alertedFlipsRef.current = new Map();
    }
  }

  // Fetch pending projections using the same query key as the Portfolio page
  const { data: projectionData } = useQuery({
    queryKey: ['portfolio', 'pending', 'projections', accountId],
    queryFn: async () => {
      const response = await portfolioApi.getPendingProjections();
      return response.data;
    },
    enabled: !!accountId && alertSettings.enableAlerts,
    refetchInterval: alertSettings.enableAlerts ? alertSettings.alertPollInterval * 1000 : false,
    staleTime: 1000 * 10, // Make data fresh for alerts check
  });

  // Watch for price changes and evaluate alert thresholds
  useEffect(() => {
    if (!alertSettings.enableAlerts || !projectionData?.flips) return;

    const flips = projectionData.flips;
    const newAlerts = [];
    let hasChanges = false;

    flips.forEach((flip) => {
      // We only alert if buy price and current sell (market) price are both available
      if (flip.buy_price && flip.current_sell_price) {
        // Calculate loss percentage (positive number means loss)
        const lossPct = ((flip.buy_price - flip.current_sell_price) / flip.buy_price) * 100;
        
        if (lossPct >= alertSettings.lossThresholdPct) {
          const lastPrice = alertedFlipsRef.current.get(flip.id);
          
          // Trigger if we haven't alerted for this flip yet, or if price dropped 5%+ further
          const shouldAlert = lastPrice === undefined || flip.current_sell_price < lastPrice * 0.95;
          
          if (shouldAlert) {
            newAlerts.push({
              id: flip.id,
              itemName: flip.item_name,
              buyPrice: flip.buy_price,
              currentPrice: flip.current_sell_price,
              quantity: flip.quantity_remaining,
              lossPct: lossPct,
              totalInvested: flip.buy_price * flip.quantity_remaining,
              currentValue: flip.current_sell_price * flip.quantity_remaining,
            });
            // Update the record with the price we alerted at
            alertedFlipsRef.current.set(flip.id, flip.current_sell_price);
            hasChanges = true;
          }
        } else {
          // If the loss is resolved (e.g. price went back up or item is updated),
          // clear it from our record so it can trigger again if it dips in the future.
          if (alertedFlipsRef.current.has(flip.id)) {
            alertedFlipsRef.current.delete(flip.id);
            hasChanges = true;
          }
        }
      }
    });

    if (hasChanges) {
      try {
        localStorage.setItem(
          'flipping_calculator_alerted_flips',
          JSON.stringify(Array.from(alertedFlipsRef.current.entries()))
        );
      } catch (e) {
        console.error('Failed to save alerted flips to localStorage:', e);
      }
    }

    if (newAlerts.length > 0) {
      setActiveAlerts((prev) => {
        // Combine old and new alerts without duplicating flip ids
        const combined = [...prev];
        newAlerts.forEach((alert) => {
          const index = combined.findIndex((a) => a.id === alert.id);
          if (index > -1) {
            combined[index] = alert; // Update existing
          } else {
            combined.push(alert);
          }
        });
        return combined;
      });

      // Execute alerts
      if (alertSettings.enableSound) {
        playAlertSound();
      }
      if (alertSettings.enableTabFlashing) {
        startTabFlashing("⚠️ CRITICAL DROP!");
      }
      if (alertSettings.enableInAppModal) {
        setShowModal(true);
      }
    }
  }, [projectionData, alertSettings]);

  // Acknowledge the alerts, dismiss modal, stop sound/flashing
  const handleAcknowledge = () => {
    setShowModal(false);
    setActiveAlerts([]);
    stopTabFlashing();
  };

  const handleGoToPortfolio = () => {
    handleAcknowledge();
    setActiveView('portfolio');
  };

  // Cleanup tab title flashing on unmount
  useEffect(() => {
    return () => {
      stopTabFlashing();
    };
  }, []);

  if (!showModal || activeAlerts.length === 0) return null;

  return (
    <div className="fixed inset-0 bg-[#04020a]/85 backdrop-blur-md flex items-center justify-center z-[9999] p-4">
      <div className="bg-card-gradient border border-luxury-goldBorder/40 rounded-3xl p-6 md:p-8 max-w-lg w-full shadow-gold-glow animate-pulse-subtle">
        
        {/* Pulsing Warning Shield */}
        <div className="flex flex-col items-center text-center mb-6">
          <div className="w-16 h-16 rounded-full bg-rose-950/80 border border-osrs-red/40 flex items-center justify-center text-3xl mb-4 animate-bounce shadow-[0_0_15px_rgba(244,63,94,0.4)]">
            ⚠️
          </div>
          <h2 className="text-xl md:text-2xl font-bold font-cinzel text-transparent bg-clip-text bg-gold-gradient tracking-wider">
            Market Crash Detected
          </h2>
          <p className="text-sm text-gray-400 font-outfit mt-1">
            One or more of your active flips has dipped below your {alertSettings.lossThresholdPct}% loss limit.
          </p>
        </div>

        {/* List of Affected Items */}
        <div className="space-y-4 max-h-[280px] overflow-y-auto pr-1 mb-6 scrollbar-thin scrollbar-thumb-luxury-purple/20 scrollbar-track-transparent">
          {activeAlerts.map((alert) => {
            const potentialLoss = alert.totalInvested - alert.currentValue;
            
            return (
              <div 
                key={alert.id} 
                className="bg-[#120e24]/75 border border-luxury-border/60 rounded-xl p-4 font-outfit relative overflow-hidden"
              >
                {/* Visual red glow stripe */}
                <div className="absolute top-0 bottom-0 left-0 w-1 bg-osrs-red"></div>
                
                <div className="flex justify-between items-start mb-2 pl-2">
                  <span className="font-bold text-luxury-gold tracking-wide text-base">{alert.itemName}</span>
                  <span className="text-osrs-red font-black text-sm px-2 py-0.5 rounded-md bg-rose-950/50 border border-osrs-red/20">
                    -{alert.lossPct.toFixed(1)}%
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-y-2 gap-x-4 pl-2 text-xs text-gray-400">
                  <div className="flex justify-between border-b border-luxury-border/10 pb-1">
                    <span>Quantity Owned:</span>
                    <span className="text-gray-200 font-semibold">{alert.quantity.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between border-b border-luxury-border/10 pb-1">
                    <span>Invested:</span>
                    <span className="text-osrs-red font-bold">{formatGP(alert.totalInvested)}</span>
                  </div>
                  <div className="flex justify-between border-b border-luxury-border/10 pb-1">
                    <span>Buy Price:</span>
                    <span className="text-gray-200 font-semibold">{alert.buyPrice.toLocaleString()} gp</span>
                  </div>
                  <div className="flex justify-between border-b border-luxury-border/10 pb-1">
                    <span>Current Price:</span>
                    <span className="text-osrs-blue font-semibold">{alert.currentPrice.toLocaleString()} gp</span>
                  </div>
                </div>

                <div className="mt-2.5 pt-2 border-t border-luxury-border/20 flex justify-between items-center text-xs pl-2">
                  <span className="text-gray-400 font-medium">Potential Loss if Sold Now:</span>
                  <span className="text-osrs-red font-extrabold text-sm">-{formatGP(potentialLoss)}</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3">
          <button 
            onClick={handleGoToPortfolio}
            className="flex-1 px-4 py-3 bg-gold-gradient hover:shadow-gold-glow text-luxury-darker font-bold font-outfit rounded-xl transition-all duration-300 transform hover:-translate-y-0.5 flex items-center justify-center gap-1.5"
          >
            💼 Go to Portfolio
          </button>
          <button 
            onClick={handleAcknowledge}
            className="flex-1 px-4 py-3 bg-[#151128] hover:bg-[#20193d] border border-luxury-border hover:border-luxury-purple/50 text-gray-300 font-bold font-outfit rounded-xl transition-all duration-300 transform hover:-translate-y-0.5"
          >
            Acknowledge Alert
          </button>
        </div>

      </div>
    </div>
  );
}
