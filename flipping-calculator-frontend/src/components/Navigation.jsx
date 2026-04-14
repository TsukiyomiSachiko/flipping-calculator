import { useEffect, useState } from 'react';
import { useAppStore } from '../stores/appStore';

export default function Navigation() {
  const { activeView, setActiveView, currentAccount, logout } = useAppStore();

  const handleLogout = () => {
    if (window.confirm('Are you sure you want to log out?')) {
      logout();
    }
  };

  const tabs = [
    { id: 'flips', label: 'Find Flips', shortLabel: 'Flips', icon: '🔍' },
    { id: 'conversions', label: 'Conversions', shortLabel: 'Convs', icon: '🛠️' },
    { id: 'portfolio', label: 'Portfolio', shortLabel: 'Portfolio', icon: '💼' },
    { id: 'history', label: 'History', shortLabel: 'History', icon: '📜' },
    { id: 'stats', label: 'Stats', shortLabel: 'Stats', icon: '📊' },
  ];

  return (
    <nav className="bg-gray-800 border-b border-gray-700 mb-4 md:mb-6">
      <div className="container mx-auto px-3 md:px-4">
        {/* Desktop: single row */}
        <div className="hidden md:flex items-center justify-between py-4">
          <div className="flex items-center gap-6">
            <h1 className="text-2xl font-bold text-osrs-gold">OSRS Flipping Calculator</h1>
            
            {/* Account Info & Logout */}
            <div className="flex items-center bg-gray-900 rounded-lg px-3 py-1.5 border border-gray-700">
              <span className="text-xs text-gray-500 mr-2 font-bold uppercase tracking-wider">Account</span>
              <span className="text-osrs-gold font-medium text-sm mr-3">{currentAccount?.name}</span>
              <button 
                className="text-gray-500 hover:text-white transition-colors text-xs uppercase font-bold border-l border-gray-700 pl-3"
                onClick={handleLogout}
              >
                Logout
              </button>
            </div>
          </div>

          <div className="flex gap-2">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  activeView === tab.id
                    ? 'bg-osrs-gold text-black'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
                onClick={() => setActiveView(tab.id)}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Mobile: stacked — title on top, tabs below */}
        <div className="md:hidden">
          <div className="py-3 flex justify-between items-center">
            <h1 className="text-lg font-bold text-osrs-gold">OSRS Flip Calc</h1>
            
            <div className="flex items-center bg-gray-900 rounded-lg px-2 py-1 border border-gray-700">
              <span className="text-osrs-gold font-medium text-xs mr-2">{currentAccount?.name}</span>
              <button 
                className="text-gray-500 hover:text-white transition-colors text-xs"
                onClick={handleLogout}
              >
                Logout
              </button>
            </div>
          </div>
          <div className="flex gap-1 pb-3">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                className={`flex-1 py-2 rounded-lg text-xs font-medium transition-colors text-center ${
                  activeView === tab.id
                    ? 'bg-osrs-gold text-black'
                    : 'bg-gray-700 text-gray-300'
                }`}
                onClick={() => setActiveView(tab.id)}
              >
                <span className="block text-base leading-none mb-1">{tab.icon}</span>
                {tab.shortLabel}
              </button>
            ))}
          </div>
        </div>
      </div>
    </nav>
  );
}