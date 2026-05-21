
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
    { id: 'longterm', label: 'Long Term', shortLabel: 'LongTerm', icon: '📅' },
    { id: 'highalch', label: 'High Alch', shortLabel: 'Alch', icon: '🔥' },
    { id: 'portfolio', label: 'Portfolio', shortLabel: 'Portfolio', icon: '💼' },
    { id: 'history', label: 'History', shortLabel: 'History', icon: '📜' },
    { id: 'stats', label: 'Stats', shortLabel: 'Stats', icon: '📊' },
  ];

  return (
    <nav className="bg-luxury-darker/70 backdrop-blur-md border-b border-luxury-border shadow-purple-glow mb-4 md:mb-6 sticky top-0 z-50">
      <div className="container mx-auto px-3 md:px-4">
        {/* Desktop: single row */}
        <div className="hidden md:flex items-center justify-between py-4">
          <div className="flex items-center gap-6">
            <h1 className="text-2xl font-black font-cinzel text-transparent bg-clip-text bg-gold-gradient tracking-wider drop-shadow-md">
              OSRS Flipping Calculator
            </h1>
            
            {/* Account Info & Logout */}
            <div className="flex items-center bg-[#0d0a1b] rounded-xl px-3 py-1.5 border border-luxury-border">
              <span className="text-[10px] text-luxury-purpleLight/60 mr-2 font-bold uppercase tracking-wider">Account</span>
              <span className="text-luxury-gold font-semibold text-sm mr-3 font-outfit">{currentAccount?.name}</span>
              <button 
                className="text-luxury-purpleLight hover:text-white transition-colors text-xs uppercase font-bold border-l border-luxury-border pl-3"
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
                className={`px-4 py-2 rounded-xl font-semibold transition-all duration-300 flex items-center gap-2 ${
                  activeView === tab.id
                    ? 'bg-gold-gradient text-luxury-darker font-bold shadow-gold-glow scale-[1.03]'
                    : 'bg-[#151128] hover:bg-[#20193d] text-gray-300 hover:text-white border border-luxury-border/60 hover:border-luxury-gold/30 hover:-translate-y-0.5'
                }`}
                onClick={() => setActiveView(tab.id)}
              >
                <span>{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Mobile: stacked — title on top, tabs below */}
        <div className="md:hidden">
          <div className="py-3 flex justify-between items-center">
            <h1 className="text-lg font-black font-cinzel text-transparent bg-clip-text bg-gold-gradient tracking-wide">
              OSRS Flip Calc
            </h1>
            
            <div className="flex items-center bg-[#0d0a1b] rounded-xl px-2.5 py-1 border border-luxury-border">
              <span className="text-luxury-gold font-semibold text-xs mr-2 font-outfit">{currentAccount?.name}</span>
              <button 
                className="text-luxury-purpleLight hover:text-white transition-colors text-xs uppercase font-bold border-l border-luxury-border pl-2"
                onClick={handleLogout}
              >
                Exit
              </button>
            </div>
          </div>
          <div className="flex gap-1 pb-3">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                className={`flex-1 py-2 rounded-xl text-[10px] font-bold transition-all duration-300 text-center ${
                  activeView === tab.id
                    ? 'bg-gold-gradient text-luxury-darker font-black shadow-gold-glow scale-[1.02]'
                    : 'bg-[#151128] text-gray-400 hover:text-white border border-luxury-border/30'
                }`}
                onClick={() => setActiveView(tab.id)}
              >
                <span className="block text-sm leading-none mb-0.5">{tab.icon}</span>
                {tab.shortLabel}
              </button>
            ))}
          </div>
        </div>
      </div>
    </nav>
  );
}