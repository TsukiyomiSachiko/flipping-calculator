import { useState, useRef, useEffect } from 'react';
import { useItemSearch } from '../hooks/useApi';

export default function ItemSearchBar({ onSelectItem }) {
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const wrapperRef = useRef(null);

  // Debounce the search query
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query.trim());
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const { data: results, isLoading } = useItemSearch(debouncedQuery);

  const handleSelect = (item) => {
    onSelectItem({ id: item.id, name: item.name });
    setQuery('');
    setDebouncedQuery('');
    setIsOpen(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      setIsOpen(false);
      e.target.blur();
    }
  };

  return (
    <div ref={wrapperRef} className="relative">
      <div className="relative">
        <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-luxury-purpleLight/60 text-sm">🔍</span>
        <input
          type="text"
          className="input w-full pl-10"
          placeholder="Search for an item..."
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => { if (query.trim()) setIsOpen(true); }}
          onKeyDown={handleKeyDown}
        />
      </div>

      {isOpen && debouncedQuery.length > 0 && (
        <div className="absolute z-50 mt-2 w-full bg-luxury-card backdrop-blur-xl border border-luxury-purple/20 rounded-xl shadow-luxury-shadow shadow-purple-glow max-h-72 overflow-y-auto">
          {isLoading && (
            <div className="p-4 text-luxury-purpleLight text-sm animate-pulse flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-luxury-gold animate-ping"></span>
              Searching Grand Exchange...
            </div>
          )}

          {!isLoading && results && results.length === 0 && (
            <div className="p-4 text-gray-400 text-sm italic">No items found</div>
          )}

          {!isLoading && results && results.map((item) => (
            <button
              key={item.id}
              className="w-full text-left px-4 py-3 hover:bg-luxury-purple/10 transition-all duration-200 flex justify-between items-center border-b border-luxury-border last:border-0 group"
              onClick={() => handleSelect(item)}
            >
              <span className="text-white font-medium group-hover:text-luxury-gold transition-colors duration-200">{item.name}</span>
              <span className="text-xs text-gray-400 flex items-center gap-2">
                {item.members ? (
                  <span className="bg-luxury-gold/15 text-luxury-gold text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded border border-luxury-gold/20">
                    Members
                  </span>
                ) : (
                  <span className="bg-luxury-purple/15 text-luxury-purpleLight text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded border border-luxury-purple/20">
                    F2P
                  </span>
                )}
                {item.ge_limit && (
                  <span className="ml-1 text-luxury-purpleLight/70 font-mono">
                    Limit: {item.ge_limit.toLocaleString()}
                  </span>
                )}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}