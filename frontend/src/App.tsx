import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Network } from 'lucide-react';
import { SearchBar } from './components/SearchBar';
import { SearchLog } from './components/SearchLog';
import { NetworkVisualization } from './components/NetworkVisualization';

interface Person {
  name: string;
}

interface PeopleResponse {
  people: Person[];
}

interface WSMessage {
  type: string;
  data: any;
}

function usePeople() {
  return useQuery<PeopleResponse>({
    queryKey: ['people'],
    queryFn: async () => {
      const res = await fetch('/api/people');
      if (!res.ok) {
        throw new Error('Failed to fetch people');
      }
      return res.json();
    },
    staleTime: 5 * 60 * 1000,
  });
}

function App() {
  const { data, isLoading, error } = usePeople();
  const [startPerson, setStartPerson] = useState<string>('');
  const [endPerson, setEndPerson] = useState<string>('');
  const [recentPeople, setRecentPeople] = useState<string[]>([]);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<WSMessage[]>([]);
  const [activePath, setActivePath] = useState<string[]>([]);
  const [exploredNodes, setExploredNodes] = useState<string[]>([]);

  const people = useMemo(() => data?.people ?? [], [data]);

  // Load recent people from localStorage on mount
  useEffect(() => {
    if (typeof window === 'undefined') return;
    try {
      const raw = window.localStorage.getItem('sd_recent_people');
      if (!raw) return;
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        setRecentPeople(parsed.filter((x) => typeof x === 'string'));
      }
    } catch {
      // ignore parse errors
    }
  }, []);

  useEffect(() => {
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [ws]);

  const handleCreateNew = async (name: string) => {
    try {
      const res = await fetch('/api/people/request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name }),
      });
      
      const data = await res.json();
      
      if (res.ok && data.success) {
        alert(data.message);
        // Refresh people list
        window.location.reload();
      } else {
        alert(data.message || 'Failed to create person');
      }
    } catch (error) {
      alert('Error: ' + (error instanceof Error ? error.message : 'Unknown error'));
    }
  };

  const handleSearch = () => {
    if (!startPerson || !endPerson) return;

    // Reset state cho một lần search mới (nhưng giữ lại lịch sử log)
    setExploredNodes([]);
    setActivePath([]);

    if (ws) {
      ws.close();
    }

    const wsUrl = window.location.protocol === 'https:' 
      ? 'wss://' + window.location.host + '/ws'
      : 'ws://' + window.location.host.replace(':5174', ':8080') + '/ws';
    
    const socket = new WebSocket(wsUrl);
    setWs(socket);
    setIsSearching(true);
    setIsConnected(false);

    socket.onopen = () => {
      setIsConnected(true);
      socket.send(JSON.stringify({ startNode: startPerson, endNode: endPerson }));
    };

    socket.onmessage = (event) => {
      const msg: WSMessage = JSON.parse(event.data);
      setMessages((prev) => [...prev, msg]);

      if (msg.type === 'node_explored') {
        const node = msg.data.node as string | undefined;
        if (node) {
          setExploredNodes((prev) => {
            const updated = prev.includes(node) ? prev : [...prev, node];
            return updated;
          });
        }
      } else if (msg.type === 'level_explored') {
        const nodes: string[] = msg.data.nodes || [];
        setExploredNodes((prev) => {
          const newSet = new Set([...prev, ...nodes]);
          const updated = Array.from(newSet);
          return updated;
        });
      } else if (msg.type === 'path_found') {
        const path: string[] = msg.data.path ?? [];
        setActivePath(path);
        // Đồng bộ lại start/end để chắc chắn trùng với title trong DB/path
        if (path.length > 0) {
          const start = path[0];
          const end = path[path.length - 1];
          setStartPerson(start);
          setEndPerson(end);

          // Cập nhật recent people (ưu tiên mới nhất, giới hạn 10)
          setRecentPeople((prev) => {
            const next = [start, end, ...prev];
            const dedup: string[] = [];
            for (const name of next) {
              if (!name) continue;
              if (!dedup.includes(name)) dedup.push(name);
              if (dedup.length >= 10) break;
            }
            if (typeof window !== 'undefined') {
              try {
                window.localStorage.setItem('sd_recent_people', JSON.stringify(dedup));
              } catch {
                // ignore quota errors
              }
            }
            return dedup;
          });
        }
        setIsSearching(false);
      } else if (msg.type === 'error') {
        setIsSearching(false);
      }
    };

    socket.onclose = () => {
      setIsConnected(false);
      setIsSearching(false);
    };

    socket.onerror = () => {
      setIsConnected(false);
      setIsSearching(false);
    };
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-800 py-8">
      <div className="max-w-7xl mx-auto px-4 space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="flex flex-col-reverse gap-4 sm:flex-row sm:gap-0 items-center justify-center space-x-3 mb-4">
            <Network className="w-10 h-10 text-blue-400" />
            <h1 className="text-4xl font-bold text-gray-100">
              Six Degrees of Wikipedia
            </h1>
          </div>
          <p className="text-lg text-gray-400 mb-2">
            Explore the threads that tie us together
          </p>
          <div className="w-24 h-1 bg-gradient-to-r from-blue-500 to-purple-500 mx-auto rounded-full" />
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
          {/* Left Column - Controls */}
          <div className="lg:col-span-2 space-y-6">
            <SearchBar
              startPerson={startPerson}
              endPerson={endPerson}
              people={people}
              recentPeople={recentPeople}
              onStartChange={setStartPerson}
              onEndChange={setEndPerson}
              onSearch={handleSearch}
              isSearching={isSearching}
              isLoading={isLoading}
              onCreateNew={handleCreateNew}
            />
            
            <SearchLog
              messages={messages}
              isConnected={isConnected}
              activePath={activePath}
              isSearching={isSearching}
            />
          </div>

          {/* Right Column - Visualization */}
          <div className="lg:col-span-3">
            <NetworkVisualization
              activePath={activePath}
              exploredNodes={exploredNodes}
              startPersonId={startPerson}
              endPersonId={endPerson}
            />
          </div>
        </div>

        {/* Footer */}
        <div className="text-center">
          <p className="text-gray-400 text-sm">
            While watching the film <em>Six Degrees of Separation</em> I came across the idea that any two people are connected by no more than six "friend of a friend" relationships. Curious, I wanted to see if that really held up. I used Wikipedia pages to test connections since all notable people have a page. It works well enough. I created a list of over ten thousand names, a small slice of the world but large enough to build some interesting visualizations. I also built this project to sharpen my Golang skills, working with goroutines, websocket connections, and writing my own BFS algorithm.
          </p>
          <p className="text-gray-400 text-sm mt-2">
            Note: A connection exists if one person's Wikipedia page mentions another person from this list. They don't need to have met or interacted for the link to count.
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;
