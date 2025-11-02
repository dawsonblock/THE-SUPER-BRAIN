import { Activity } from 'lucide-react';

export default function MonitorPage() {
  return (
    <div className="p-6">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">System Monitor</h1>
        <p className="text-gray-500 mb-8">Real-time metrics and performance monitoring</p>

        <div className="card text-center py-12">
          <Activity className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Coming Soon</h2>
          <p className="text-gray-500">
            Prometheus metrics visualization with latency, confidence, and refusal rate tracking.
          </p>
        </div>
      </div>
    </div>
  );
}

