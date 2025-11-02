import { Users } from 'lucide-react';

export default function MultiAgentPage() {
  return (
    <div className="p-6">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Multi-Agent Operations</h1>
        <p className="text-gray-500 mb-8">Compare solver outputs and view judge selection</p>

        <div className="card text-center py-12">
          <Users className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Coming Soon</h2>
          <p className="text-gray-500">
            Side-by-side agent comparison with confidence scores, citations, and judge reasoning.
          </p>
        </div>
      </div>
    </div>
  );
}

