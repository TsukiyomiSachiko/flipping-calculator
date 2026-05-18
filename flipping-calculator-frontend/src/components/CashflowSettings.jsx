import { useState, useEffect } from 'react';
import { useSettings, useSetCashflowSettings } from '../hooks/useApi';

export default function CashflowSettings() {
  const { data: settings } = useSettings();
  const setCashflowMutation = useSetCashflowSettings();
  
  const [isEditing, setIsEditing] = useState(false);
  const [profitPct, setProfitPct] = useState('0');
  const [lossPct, setLossPct] = useState('0');

  useEffect(() => {
    if (settings && !isEditing) {
      setProfitPct((settings.profit_take_pct || 0).toString());
      setLossPct((settings.loss_refill_pct || 0).toString());
    }
  }, [settings, isEditing]);

  const handleSave = () => {
    let p = parseFloat(profitPct);
    let l = parseFloat(lossPct);
    
    if (isNaN(p) || p < 0) p = 0;
    if (p > 100) p = 100;
    
    if (isNaN(l) || l < 0) l = 0;
    if (l > 100) l = 100;
    
    setCashflowMutation.mutate({
      profit_take_pct: p,
      loss_refill_pct: l
    });
    
    setIsEditing(false);
  };

  const handleCancel = () => {
    setIsEditing(false);
    if (settings) {
      setProfitPct((settings.profit_take_pct || 0).toString());
      setLossPct((settings.loss_refill_pct || 0).toString());
    }
  };

  return (
    <div className="card">
      <div className="flex justify-between items-start mb-2">
        <h3 className="text-sm text-gray-400">Cashflow Rules</h3>
        {!isEditing && (
          <button 
            className="text-xs text-osrs-blue hover:underline"
            onClick={() => setIsEditing(true)}
          >
            Edit
          </button>
        )}
      </div>

      {isEditing ? (
        <div className="space-y-3 mt-3">
          <div>
            <label className="text-xs text-gray-400 block mb-1">Profit to Keep (%)</label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                min="0"
                max="100"
                step="0.1"
                className="input text-sm w-full"
                value={profitPct}
                onChange={(e) => setProfitPct(e.target.value)}
              />
              <span className="text-gray-400">%</span>
            </div>
            <p className="text-[10px] text-gray-500 mt-1">Amount of profit withdrawn from stack</p>
          </div>
          
          <div>
            <label className="text-xs text-gray-400 block mb-1">Loss to Refill (%)</label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                min="0"
                max="100"
                step="0.1"
                className="input text-sm w-full"
                value={lossPct}
                onChange={(e) => setLossPct(e.target.value)}
              />
              <span className="text-gray-400">%</span>
            </div>
            <p className="text-[10px] text-gray-500 mt-1">Amount of loss refilled to stack</p>
          </div>

          <div className="flex gap-2 pt-2">
            <button 
              className="btn btn-primary text-xs py-1 flex-1"
              onClick={handleSave}
              disabled={setCashflowMutation.isPending}
            >
              {setCashflowMutation.isPending ? 'Saving...' : 'Save Rules'}
            </button>
            <button 
              className="btn btn-secondary text-xs py-1 flex-1"
              onClick={handleCancel}
              disabled={setCashflowMutation.isPending}
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-3 mt-2">
          <div>
            <p className="text-xs text-gray-500">Profit Kept</p>
            <p className="text-lg font-bold text-osrs-green">
              {settings?.profit_take_pct || 0}%
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Loss Refilled</p>
            <p className="text-lg font-bold text-osrs-red">
              {settings?.loss_refill_pct || 0}%
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
