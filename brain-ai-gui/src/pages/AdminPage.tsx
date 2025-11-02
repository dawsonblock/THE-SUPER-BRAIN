import { Settings } from 'lucide-react';

export default function AdminPage() {
  return (
    <div className="p-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Admin & Configuration</h1>
        <p className="text-gray-500 mb-8">System controls and configuration management</p>

        <div className="card text-center py-12">
          <Settings className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Coming Soon</h2>
          <p className="text-gray-500">
            Live configuration editing, kill switch control, and cache management.
          </p>
        </div>
      </div>
    </div>
  );
}

