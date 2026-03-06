import { useEffect, useMemo, useRef, useState } from 'react';

interface Person {
  name: string;
}

interface SearchableDropdownProps {
  label: string;
  value: string;
  people: Person[];
  onChange: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  recentNames?: string[];
  onCreateNew?: (name: string) => void;
}

// Lightweight client-side searchable dropdown (no extra API calls)
export const SearchableDropdown: React.FC<SearchableDropdownProps> = ({
  label,
  value,
  people,
  onChange,
  placeholder = 'Select...',
  disabled = false,
  recentNames,
  onCreateNew,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const containerRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const listRef = useRef<HTMLDivElement | null>(null);
  const [visibleCount, setVisibleCount] = useState(50);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchTerm('');
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Reset pagination when results or query change
  useEffect(() => {
    setVisibleCount(50);
    if (listRef.current) {
      listRef.current.scrollTop = 0;
    }
  }, [searchTerm, people]);

  const lowerSearch = searchTerm.toLowerCase();

  const filteredPeople = useMemo(() => {
    if (!lowerSearch) return people;
    return people.filter((p) => p.name.toLowerCase().includes(lowerSearch));
  }, [people, lowerSearch]);

  // Recent options: từ recentNames, ưu tiên lên trên, filter theo search term
  const recentOptions = useMemo(() => {
    if (!recentNames || recentNames.length === 0) return [] as Person[];
    const seen = new Set<string>();
    const res: Person[] = [];
    for (const name of recentNames) {
      if (!name || seen.has(name)) continue;
      if (lowerSearch && !name.toLowerCase().includes(lowerSearch)) continue;
      const found = people.find((p) => p.name === name);
      res.push(found || { name });
      seen.add(name);
    }
    return res;
  }, [recentNames, lowerSearch, people]);

  const regularOptions = useMemo(() => {
    if (recentOptions.length === 0) return filteredPeople;
    const recentSet = new Set(recentOptions.map((p) => p.name));
    return filteredPeople.filter((p) => !recentSet.has(p.name));
  }, [filteredPeople, recentOptions]);

  const visiblePeople = useMemo(
    () => regularOptions.slice(0, visibleCount),
    [regularOptions, visibleCount],
  );

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const el = e.currentTarget;
    const nearBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - 16;
    if (nearBottom && visibleCount < filteredPeople.length) {
      setVisibleCount((prev) => Math.min(prev + 50, filteredPeople.length));
    }
  };

  const handleInputClick = () => {
    if (disabled) return;
    if (!isOpen) {
      setIsOpen(true);
      inputRef.current?.focus();
    }
  };

  const handleSelect = (name: string) => {
    onChange(name);
    setIsOpen(false);
    setSearchTerm('');
  };

  const displayValue = useMemo(() => {
    if (isOpen) return searchTerm;
    return value || '';
  }, [isOpen, searchTerm, value]);

  return (
    <div className="relative" ref={containerRef}>
      <label className="block text-sm text-gray-400 mb-2">{label}</label>

      <div
        className={`w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-gray-100 flex items-center justify-between cursor-text ${
          disabled ? 'opacity-50 cursor-not-allowed' : 'hover:border-gray-500'
        }`}
        onClick={handleInputClick}
      >
        <input
          ref={inputRef}
          type="text"
          value={displayValue}
          onChange={(e) => setSearchTerm(e.target.value)}
          onFocus={() => !disabled && setIsOpen(true)}
          placeholder={placeholder}
          disabled={disabled}
          className="flex-1 bg-transparent outline-none text-gray-100 placeholder-gray-400"
        />
        <span
          className={`ml-2 text-gray-400 transition-transform ${
            isOpen ? 'rotate-180' : ''
          }`}
        >
          ▾
        </span>
      </div>

      {isOpen && !disabled && (
        <div
          ref={listRef}
          onScroll={handleScroll}
          className="absolute z-10 w-full mt-1 bg-gray-900 border border-gray-700 rounded-lg shadow-xl max-h-60 overflow-y-auto"
        >
          {recentOptions.length === 0 && visiblePeople.length === 0 ? (
            <div className="px-4 py-2">
              <div className="text-sm text-gray-400 text-center mb-2">No results</div>
              {searchTerm.trim() && onCreateNew && (
                <button
                  onClick={() => {
                    onCreateNew(searchTerm.trim());
                    setIsOpen(false);
                    setSearchTerm('');
                  }}
                  className="w-full px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
                >
                  Create new: {searchTerm.trim()}
                </button>
              )}
            </div>
          ) : (
            <>
              {recentOptions.length > 0 && (
                <div className="border-b border-gray-700">
                  <div className="px-4 py-1 text-xs uppercase tracking-wide text-gray-400 bg-gray-800/80 sticky top-0">
                    Recent
                  </div>
                  {recentOptions.map((p) => (
                    <div
                      key={`recent-${p.name}`}
                      onClick={() => handleSelect(p.name)}
                      className="px-4 py-2 text-sm text-gray-100 hover:bg-gray-700 cursor-pointer"
                    >
                      {p.name}
                    </div>
                  ))}
                </div>
              )}

              {visiblePeople.length > 0 && (
                <>
                  {recentOptions.length > 0 && (
                    <div className="px-4 py-1 text-xs uppercase tracking-wide text-gray-500 bg-gray-900/90">
                      All
                    </div>
                  )}
                  {visiblePeople.map((p) => (
                    <div
                      key={p.name}
                      onClick={() => handleSelect(p.name)}
                      className="px-4 py-2 text-sm text-gray-100 hover:bg-gray-700 cursor-pointer"
                    >
                      {p.name}
                    </div>
                  ))}
                </>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}

