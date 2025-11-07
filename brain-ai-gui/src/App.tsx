import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import {
  MessageSquare,
  Search,
  Upload,
  Users,
  Activity,
  Settings,
  Brain,
} from 'lucide-react';
import { cn } from './lib/utils';

// Pages
import ChatPage from './pages/ChatPage';
import SearchPage from './pages/SearchPage';
import UploadPage from './pages/UploadPage';
import MultiAgentPage from './pages/MultiAgentPage';
import MonitorPage from './pages/MonitorPage';
import AdminPage from './pages/AdminPage';

function Navigation() {
  const location = useLocation();

  const navItems = [
    { path: '/', icon: MessageSquare, label: 'Chat' },
    { path: '/search', icon: Search, label: 'Search' },
    { path: '/upload', icon: Upload, label: 'Upload' },
    { path: '/multi-agent', icon: Users, label: 'Multi-Agent' },
    { path: '/monitor', icon: Activity, label: 'Monitor' },
    { path: '/admin', icon: Settings, label: 'Admin' },
  ];

  return (
    <nav className="w-64 bg-white border-r border-gray-200 flex flex-col">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center gap-3">
          <Brain className="w-8 h-8 text-primary-600" />
          <div>
            <h1 className="text-xl font-bold text-gray-900">Brain-AI</h1>
            <p className="text-xs text-gray-500">RAG++ Control Center</p>
          </div>
        </div>
      </div>

      <div className="flex-1 p-4 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;

          return (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                'flex items-center gap-3 px-4 py-3 rounded-lg transition-all',
                isActive
                  ? 'bg-primary-50 text-primary-700 font-medium'
                  : 'text-gray-600 hover:bg-gray-50'
              )}
            >
              <Icon className="w-5 h-5" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </div>

      <div className="p-4 border-t border-gray-200">
        <div className="text-xs text-gray-500">
          <p>Version 4.5.0</p>
          <p>RAG++ Production</p>
          <p className="text-green-600 font-semibold mt-1">✨ Optimized</p>
        </div>
      </div>
    </nav>
  );
}

function App() {
  return (
    <BrowserRouter>
      <div className="h-screen flex overflow-hidden bg-gray-50">
        <Navigation />
        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<ChatPage />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/multi-agent" element={<MultiAgentPage />} />
            <Route path="/monitor" element={<MonitorPage />} />
            <Route path="/admin" element={<AdminPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;

