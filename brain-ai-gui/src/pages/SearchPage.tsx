import { Search } from 'lucide-react';

export default function SearchPage() {
  return (
    <div className="p-6">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Search & RAG Panel</h1>
        <p className="text-gray-500 mb-8">Advanced search with retrieved context inspection</p>

        <div className="card text-center py-12">
          <Search className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Coming Soon</h2>
          <p className="text-gray-500">
            Advanced search interface with context chunks, confidence scores, and reranking visualization.
          </p>
        </div>
      </div>
    </div>
  );
}

