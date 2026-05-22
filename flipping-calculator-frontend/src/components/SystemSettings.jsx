import { usePriceHistoryStats, useTriggerPoll, useSetPollingEnabled } from '../hooks/useApi';
import { useAppStore } from '../stores/appStore';
import { playAlertSound } from '../utils/sound';

export default function SystemSettings() {
  const { data: stats, isLoading } = usePriceHistoryStats();
  const triggerPoll = useTriggerPoll();
  const setEnabled = useSetPollingEnabled();

  const { alertSettings, setAlertSettings } = useAppStore();

  if (isLoading) return <div className="card animate-pulse h-32 mb-6"></div>;

  const polling = stats?.polling || {};
  const db = stats?.database || {};

  const handleToggleAlerts = () => {
    setAlertSettings({ enableAlerts: !alertSettings.enableAlerts });
  };

  const handleToggleSound = () => {
    setAlertSettings({ enableSound: !alertSettings.enableSound });
  };

  const handleToggleTabFlashing = () => {
    setAlertSettings({ enableTabFlashing: !alertSettings.enableTabFlashing });
  };

  const handleToggleInAppModal = () => {
    setAlertSettings({ enableInAppModal: !alertSettings.enableInAppModal });
  };

  const handleThresholdChange = (e) => {
    const val = parseFloat(e.target.value);
    if (!isNaN(val) && val >= 0) {
      setAlertSettings({ lossThresholdPct: val });
    }
  };

  const handleIntervalChange = (e) => {
    const val = parseInt(e.target.value);
    if (!isNaN(val) && val >= 5) { // minimum 5 seconds to avoid rate limiting
      setAlertSettings({ alertPollInterval: val });
    }
  };

  return (
    <div className="space-y-4 md:space-y-6 mb-4 md:mb-6">
      {/* System Status Card */}
      <div className="card">
        <h2 className="text-lg font-bold text-osrs-gold mb-4 flex items-center gap-2">
          ⚙️ System Status
          {polling.polling_enabled && (
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-osrs-green opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-osrs-green"></span>
            </span>
          )}
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Polling Control */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Price Polling</h3>
            <div className="flex items-center justify-between bg-gray-900/50 p-3 rounded-lg border border-gray-700">
              <div>
                <p className="text-sm font-medium">Automatic Polling</p>
                <p className="text-xs text-gray-500">Every {polling.poll_interval_minutes} minutes</p>
              </div>
              <button
                onClick={() => setEnabled.mutate(!polling.polling_enabled)}
                disabled={setEnabled.isPending}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${
                  polling.polling_enabled ? 'bg-osrs-green' : 'bg-gray-600'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    polling.polling_enabled ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
            
            <button
              onClick={() => triggerPoll.mutate()}
              disabled={triggerPoll.isPending}
              className="btn btn-secondary w-full text-xs flex items-center justify-center gap-2 py-2"
            >
              {triggerPoll.isPending ? '⏳ Polling...' : '🔄 Trigger Manual Poll'}
            </button>
          </div>

          {/* Database Stats */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Local Database</h3>
            <div className="bg-gray-900/50 p-3 rounded-lg border border-gray-700 space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Total Snapshots:</span>
                <span className="font-mono text-osrs-blue">{db.total_records?.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Unique Items:</span>
                <span className="font-mono text-osrs-blue">{db.unique_items?.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Retention:</span>
                <span className="text-gray-200">Last 30 Days</span>
              </div>
            </div>
          </div>

          {/* Activity */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Latest Activity</h3>
            <div className="bg-gray-900/50 p-3 rounded-lg border border-gray-700">
              <p className="text-xs text-gray-400 mb-1">Last Successful Poll:</p>
              <p className="text-sm font-medium">
                {polling.last_poll_time 
                  ? new Date(polling.last_poll_time.endsWith('Z') ? polling.last_poll_time : `${polling.last_poll_time}Z`).toLocaleTimeString() 
                  : 'Never'}
              </p>
              <div className="mt-2 pt-2 border-t border-gray-700/50">
                <p className="text-xs text-gray-400 mb-1">Newest Data point:</p>
                <p className="text-sm font-medium">
                  {db.newest_date 
                    ? new Date(db.newest_date.endsWith('Z') ? db.newest_date : `${db.newest_date}Z`).toLocaleString() 
                    : 'N/A'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Market Crash Alerts Card */}
      <div className="card">
        <h2 className="text-lg font-bold text-osrs-gold mb-4 flex items-center gap-2">
          🔔 Market Crash Alerts
          {alertSettings.enableAlerts && (
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-osrs-red opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-osrs-red"></span>
            </span>
          )}
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 font-outfit">
          {/* Controls & Threshold */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Evaluation</h3>
            <div className="flex items-center justify-between bg-gray-900/50 p-3 rounded-lg border border-gray-700">
              <div>
                <p className="text-sm font-medium">Enable Alerts</p>
                <p className="text-xs text-gray-500">Monitor active flip losses</p>
              </div>
              <button
                onClick={handleToggleAlerts}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${
                  alertSettings.enableAlerts ? 'bg-osrs-red' : 'bg-gray-600'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    alertSettings.enableAlerts ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs text-gray-400 font-semibold uppercase tracking-wider block">Loss Trigger Threshold (%)</label>
              <div className="relative">
                <input
                  type="number"
                  min="0.1"
                  max="100"
                  step="0.5"
                  className="input w-full pr-12 text-sm"
                  value={alertSettings.lossThresholdPct}
                  onChange={handleThresholdChange}
                  disabled={!alertSettings.enableAlerts}
                />
                <span className="absolute right-3 top-2.5 text-xs text-gray-500 font-semibold">% Drop</span>
              </div>
            </div>
          </div>

          {/* Notification Channels */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Alert Channels</h3>
            
            <div className="space-y-2 bg-[#0d0a1b]/60 border border-luxury-border/30 rounded-xl p-3">
              {/* Sound Toggle */}
              <div className="flex items-center justify-between border-b border-luxury-border/10 pb-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">Sound Notification</span>
                  <button 
                    onClick={playAlertSound}
                    className="px-2 py-0.5 bg-[#151128] hover:bg-[#20193d] rounded border border-luxury-border text-[10px] text-luxury-gold tracking-wider hover:border-luxury-gold/50 transition-colors uppercase font-bold"
                    title="Test synthesized warning chime"
                  >
                    🔊 Test
                  </button>
                </div>
                <button
                  onClick={handleToggleSound}
                  disabled={!alertSettings.enableAlerts}
                  className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none ${
                    alertSettings.enableSound && alertSettings.enableAlerts ? 'bg-luxury-purple' : 'bg-gray-600'
                  }`}
                >
                  <span
                    className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
                      alertSettings.enableSound && alertSettings.enableAlerts ? 'translate-x-5' : 'translate-x-0.5'
                    }`}
                  />
                </button>
              </div>

              {/* Tab Flashing Toggle */}
              <div className="flex items-center justify-between border-b border-luxury-border/10 pb-2">
                <span className="text-sm font-medium">Tab Title Flashing</span>
                <button
                  onClick={handleToggleTabFlashing}
                  disabled={!alertSettings.enableAlerts}
                  className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none ${
                    alertSettings.enableTabFlashing && alertSettings.enableAlerts ? 'bg-luxury-purple' : 'bg-gray-600'
                  }`}
                >
                  <span
                    className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
                      alertSettings.enableTabFlashing && alertSettings.enableAlerts ? 'translate-x-5' : 'translate-x-0.5'
                    }`}
                  />
                </button>
              </div>

              {/* In-App Modal Toggle */}
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Premium Visual Modal</span>
                <button
                  onClick={handleToggleInAppModal}
                  disabled={!alertSettings.enableAlerts}
                  className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none ${
                    alertSettings.enableInAppModal && alertSettings.enableAlerts ? 'bg-luxury-purple' : 'bg-gray-600'
                  }`}
                >
                  <span
                    className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
                      alertSettings.enableInAppModal && alertSettings.enableAlerts ? 'translate-x-5' : 'translate-x-0.5'
                    }`}
                  />
                </button>
              </div>
            </div>
          </div>

          {/* Polling & Information */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Polling Frequency</h3>
            
            <div className="space-y-1.5">
              <label className="text-xs text-gray-400 font-semibold uppercase tracking-wider block">Check Interval (seconds)</label>
              <div className="relative">
                <input
                  type="number"
                  min="5"
                  max="3600"
                  step="5"
                  className="input w-full pr-16 text-sm"
                  value={alertSettings.alertPollInterval}
                  onChange={handleIntervalChange}
                  disabled={!alertSettings.enableAlerts}
                />
                <span className="absolute right-3 top-2.5 text-xs text-gray-500 font-semibold">Seconds</span>
              </div>
            </div>

            <p className="text-[10px] text-gray-500 leading-normal bg-gray-950/20 border border-luxury-border/10 p-2.5 rounded-lg">
              ℹ️ OS notifications are bypassed by using synthesized audio alerts, flashing browser tabs, and modal viewport overlays. These alerts display even if Windows Notifications are disabled.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

