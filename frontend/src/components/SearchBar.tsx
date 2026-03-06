import { Search } from 'lucide-react';
import { SearchableDropdown } from './SearchableDropdown';

interface Person {
  name: string;
}

interface SearchBarProps {
  startPerson: string;
  endPerson: string;
  people: Person[];
  recentPeople: string[];
  onStartChange: (value: string) => void;
  onEndChange: (value: string) => void;
  onSearch: () => void;
  isSearching: boolean;
  isLoading: boolean;
  onCreateNew?: (name: string) => void;
}

export const SearchBar: React.FC<SearchBarProps> = ({
  startPerson,
  endPerson,
  people,
  recentPeople,
  onStartChange,
  onEndChange,
  onSearch,
  isSearching,
  isLoading,
  onCreateNew,
}) => {
  const isSearchEnabled = !!startPerson && !!endPerson && !isSearching;

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
      <h2 className="text-xl font-semibold text-gray-100 mb-4">Pathfinding Search</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <SearchableDropdown
          label="Start Person"
          value={startPerson}
          people={people}
          onChange={onStartChange}
          placeholder="Select start..."
          disabled={isLoading}
          recentNames={recentPeople}
          onCreateNew={onCreateNew}
        />

        <SearchableDropdown
          label="End Person"
          value={endPerson}
          people={people}
          onChange={onEndChange}
          placeholder="Select end..."
          disabled={isLoading}
          recentNames={recentPeople}
          onCreateNew={onCreateNew}
        />
      </div>

      <button
        onClick={onSearch}
        disabled={!isSearchEnabled}
        className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3 px-6 rounded-lg flex items-center justify-center space-x-2 transition-all"
      >
        <Search className="w-5 h-5" />
        <span>{isSearching ? 'Searching...' : 'Start Search'}</span>
      </button>
    </div>
  );
};
