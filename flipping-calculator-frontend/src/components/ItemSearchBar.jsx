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
        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">🔍</span>
        <input
          type="text"
          className="input w-full pl-9"
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
        <div className="absolute z-50 mt-1 w-full bg-gray-800 border border-gray-700 rounded-lg shadow-lg max-h-72 overflow-y-auto">
          {isLoading && (
            <div className="p-3 text-gray-400 text-sm">Searching...</div>
          )}

          {!isLoading && results && results.length === 0 && (
            <div className="p-3 text-gray-400 text-sm">No items found</div>
          )}

          {!isLoading && results && results.map((item) => (
            <button
              key={item.id}
              className="w-full text-left px-4 py-2.5 hover:bg-gray-700 transition-colors flex justify-between items-center border-b border-gray-700 last:border-0"
              onClick={() => handleSelect(item)}
            >
              <span className="text-white font-medium">{item.name}</span>
              <span className="text-xs text-gray-400 flex items-center gap-2">
                {item.members
                  ? <span className="text-yellow-400">⭐ Members</span>
                  : <span>F2P</span>
                }
                {item.ge_limit && (
                  <span className="ml-1">Limit: {item.ge_limit.toLocaleString()}</span>
                )}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}