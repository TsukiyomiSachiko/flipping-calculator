import {} from 'react';
import { usePriceHistoryStats, useTriggerPoll, useSetPollingEnabled } from '../hooks/useApi';

export default function SystemSettings() {
  const { data: stats, isLoading } = usePriceHistoryStats();
  const triggerPoll = useTriggerPoll();
  const setEnabled = useSetPollingEnabled();

  if (isLoading) return <div className="card animate-pulse h-32"></div>;

  const polling = stats?.polling || {};
  const db = stats?.database || {};

  return (
    <div className="card mb-6">
      <h2 className="text-lg font-bold text-osrs-gold mb-4 flex items-center gap-2">
        ⚙️ System Status
        {polling.polling_enabled && (
          <span className="flex h-2 w-2">
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
  );
}
