import { useEffect, useRef, useState } from 'react';

interface LogEntry {
  timestamp: string;
  message?: string;
  type: 'info' | 'path' | 'error' | 'level';
  pathNodes?: string[];
  steps?: number;
}

interface SearchLogProps {
  messages: any[];
  isConnected: boolean;
  activePath: string[];
  isSearching: boolean;
}

const buildWikiUrl = (name: string) =>
  `https://en.wikipedia.org/wiki/${encodeURIComponent(name.replace(/ /g, '_'))}`;

export const SearchLog: React.FC<SearchLogProps> = ({
  messages,
  isConnected,
  activePath,
  isSearching,
}) => {
  const logRef = useRef<HTMLDivElement>(null);
  const [logEntries, setLogEntries] = useState<LogEntry[]>([]);

  useEffect(() => {
    const newEntries: LogEntry[] = [];
    
    messages.forEach((msg) => {
      const timestamp = new Date().toLocaleTimeString('en-US', { 
        hour12: false, 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit' 
      });

      if (msg.type === 'path_found') {
        const data = msg.data;
        const path: string[] = data.path ?? [];
        newEntries.push({
          timestamp,
          type: 'path',
          message: 'Path found:',
          pathNodes: path,
          steps: data.length,
        });
      } else if (msg.type === 'error') {
        const raw = String(msg.data ?? '');
        const friendly =
          raw.toLowerCase().includes('no path found')
            ? 'No path found between the selected people.'
            : `Error: ${raw}`;
        newEntries.push({
          timestamp,
          type: 'error',
          message: friendly,
        });
      }
    });

    setLogEntries(newEntries);

    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [messages, activePath]);

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-100">Search Log</h2>
        <div className="flex items-center space-x-3">
          {isSearching && (
            <div className="flex items-center space-x-1 text-blue-300 text-sm">
              <span className="w-3 h-3 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
              <span>Searching...</span>
            </div>
          )}
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-sm text-gray-400">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
      </div>
      
      <div 
        ref={logRef}
        className="bg-black/40 rounded-lg border border-gray-700 p-4 h-[400px] overflow-y-auto font-mono text-sm"
      >
        {logEntries.length === 0 ? (
          <p className="text-gray-500">
            {isSearching ? 'Searching for path...' : 'No search activity yet...'}
          </p>
        ) : (
          <div className="space-y-2">
            {logEntries.map((entry, idx) => (
              <div 
                key={idx} 
                className={`${
                  entry.type === 'path' ? 'text-green-400' : 
                  entry.type === 'error' ? 'text-red-400' : 
                  'text-gray-300'
                }`}
              >
                <span className="text-gray-500">{entry.timestamp}</span>{' '}
                {entry.pathNodes && entry.pathNodes.length > 0 ? (
                  <span>
                    <span>{entry.message}</span>{' '}
                    <span className="text-gray-200">
                      {entry.pathNodes.map((name, i) => (
                        <span key={name + i}>
                          {i > 0 && <span className="text-gray-500"> {'→'} </span>}
                          <a
                            href={buildWikiUrl(name)}
                            target="_blank"
                            rel="noreferrer"
                            className="underline hover:text-blue-300"
                          >
                            {name}
                          </a>
                        </span>
                      ))}
                      {typeof entry.steps === 'number' && (
                        <span className="text-gray-400"> ({entry.steps} steps)</span>
                      )}
                    </span>
                  </span>
                ) : (
                  entry.message
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
