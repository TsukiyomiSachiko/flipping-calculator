import { useState } from 'react';
import { useConversions, useConversionSync } from '../hooks/useApi';
import { formatNumber } from '../utils/formatters';

export default function ConversionsView() {
  const { data: conversions, isLoading, error, refetch } = useConversions();
  const syncMutation = useConversionSync();
  const [searchTerm, setSearchTerm] = useState('');

  const filteredConversions = conversions?.filter(c => 
    c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.category?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleSync = async () => {
    try {
      await syncMutation.mutateAsync();
      refetch();
    } catch (err) {
      console.error('Failed to sync conversions:', err);
    }
  };

  if (isLoading) {
    return (
      <div className="card text-center py-12">
        <p className="text-gray-400">Loading conversions...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card text-center py-12">
        <p className="text-red-400">Error: {error.message}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="relative w-full md:w-96">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">🔍</span>
          <input
            type="text"
            className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-10 pr-4 py-2 text-white focus:border-osrs-gold focus:outline-none"
            placeholder="Search conversions (e.g. mahogany, planks)..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        
        <button
          onClick={handleSync}
          disabled={syncMutation.isPending}
          className="w-full md:w-auto bg-gray-700 hover:bg-gray-600 text-osrs-gold font-bold py-2 px-6 rounded-lg transition-colors border border-gray-600 flex items-center justify-center gap-2"
        >
          {syncMutation.isPending ? 'Syncing...' : '🔄 Sync from Wiki'}
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {filteredConversions?.map((conv) => (
          <div key={conv.id} className="card hover:border-gray-500 transition-colors">
            <div className="flex flex-col lg:flex-row justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-lg font-bold text-osrs-gold">{conv.name}</h3>
                  <span className="text-xs bg-gray-700 text-gray-300 px-2 py-0.5 rounded uppercase font-bold tracking-wider">
                    {conv.category}
                  </span>
                  {conv.members && (
                    <span className="text-xs bg-blue-900/30 text-blue-400 px-2 py-0.5 rounded font-bold">
                      MEMBERS
                    </span>
                  )}
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  {/* Inputs */}
                  <div className="bg-gray-900/50 rounded-lg p-3 border border-gray-800">
                    <h4 className="text-xs font-bold text-gray-500 uppercase mb-2 tracking-widest">Inputs</h4>
                    <ul className="space-y-1">
                      {conv.inputs.map((inp, idx) => (
                        <li key={idx} className="flex justify-between text-sm">
                          <span className="text-osrs-red">{formatNumber(inp.quantity)} x {inp.item_name}</span>
                          <span className="text-gray-400">{formatNumber(inp.price)} gp</span>
                        </li>
                      ))}
                    </ul>
                    <div className="mt-2 pt-2 border-t border-gray-800 flex justify-between font-bold text-sm">
                      <span className="text-gray-400">Total Cost</span>
                      <span className="text-osrs-red">{formatNumber(conv.total_cost)} gp</span>
                    </div>
                  </div>

                  {/* Outputs */}
                  <div className="bg-gray-900/50 rounded-lg p-3 border border-gray-800">
                    <h4 className="text-xs font-bold text-gray-500 uppercase mb-2 tracking-widest">Outputs</h4>
                    <ul className="space-y-1">
                      {conv.outputs.map((outp, idx) => (
                        <li key={idx} className="flex justify-between text-sm">
                          <span className="text-osrs-green">{formatNumber(outp.quantity)} x {outp.item_name}</span>
                          <span className="text-gray-400">{formatNumber(outp.price)} gp</span>
                        </li>
                      ))}
                    </ul>
                    <div className="mt-2 pt-2 border-t border-gray-800 flex justify-between font-bold text-sm">
                      <span className="text-gray-400">Net Revenue</span>
                      <span className="text-osrs-green">{formatNumber(conv.total_revenue)} gp</span>
                    </div>
                  </div>
                </div>

                <div className="flex flex-wrap gap-4 text-sm text-gray-400">
                  <div className="flex items-center gap-1">
                    <span className="font-bold text-gray-300">Rate:</span>
                    <span>{formatNumber(conv.conversion_rate_per_hour)} conversions/hr</span>
                  </div>
                  {/* 
                  {conv.skill_required && (
                    <div className="flex items-center gap-1">
                      <span className="font-bold text-gray-300">Requirement:</span>
                      <span>Level {conv.level_required} {conv.skill_required}</span>
                    </div>
                  )} 
                  */}
                  <a 
                    href={conv.wiki_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-osrs-gold hover:underline flex items-center gap-1"
                  >
                    Wiki Guide ↗
                  </a>
                </div>
              </div>

              <div className="lg:w-64 flex lg:flex-col justify-between items-end border-t lg:border-t-0 lg:border-l border-gray-700 pt-4 lg:pt-0 lg:pl-6">
                <div className="text-right">
                  <div className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-1">Profit Per Hour</div>
                  <div className={`text-2xl font-black ${conv.profit_per_hour > 0 ? 'text-osrs-green' : 'text-osrs-red'}`}>
                    {formatNumber(conv.profit_per_hour)} <span className="text-sm">gp</span>
                  </div>
                  <div className="text-sm text-gray-400 mt-1">
                    ROI: <span className={conv.roi > 0 ? 'text-osrs-green' : 'text-osrs-red'}>{conv.roi}%</span>
                  </div>
                </div>
                
                <div className="text-right text-xs text-gray-500">
                  Per item: <span className={conv.profit_per_conversion > 0 ? 'text-osrs-green' : 'text-osrs-red'}>
                    {formatNumber(Math.round(conv.profit_per_conversion))} gp
                  </span>
                </div>
              </div>
            </div>
          </div>
        ))}
        {filteredConversions?.length === 0 && (
          <div className="card text-center py-12">
            <p className="text-gray-400">No conversions found matching &quot;{searchTerm}&quot;</p>
          </div>
        )}
      </div>
    </div>
  );
}
