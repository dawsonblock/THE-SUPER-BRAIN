import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Send, Loader2, CheckCircle, XCircle, Zap, Target } from 'lucide-react';
import apiClient from '@/lib/api';
import { formatLatency, formatConfidence, getConfidenceBadgeClass, cn } from '@/lib/utils';
import type { QueryResponse } from '@/types';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  response?: QueryResponse;
  timestamp: Date;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [mode, setMode] = useState<'fast' | 'accuracy'>('fast');

  const queryMutation = useMutation({
    mutationFn: apiClient.query,
    onSuccess: (data, _variables) => {
      const assistantMessage: Message = {
        id: Date.now().toString() + '-assistant',
        role: 'assistant',
        content: data.answer,
        response: data,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || queryMutation.isPending) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    queryMutation.mutate({ query: input });
    setInput('');
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Chat</h1>
            <p className="text-sm text-gray-500">RAG++ powered conversational AI</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setMode('fast')}
              className={cn(
                'flex items-center gap-2 px-4 py-2 rounded-lg transition-all',
                mode === 'fast'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              )}
            >
              <Zap className="w-4 h-4" />
              Fast Mode
            </button>
            <button
              onClick={() => setMode('accuracy')}
              className={cn(
                'flex items-center gap-2 px-4 py-2 rounded-lg transition-all',
                mode === 'accuracy'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              )}
            >
              <Target className="w-4 h-4" />
              Accuracy Mode
            </button>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mb-4">
              <Send className="w-8 h-8 text-primary-600" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Start a conversation</h2>
            <p className="text-gray-500 max-w-md">
              Ask questions and get evidence-based answers powered by the RAG++ architecture.
            </p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={cn(
              'flex gap-4',
              message.role === 'user' ? 'justify-end' : 'justify-start'
            )}
          >
            {message.role === 'assistant' && (
              <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center text-white font-semibold flex-shrink-0">
                AI
              </div>
            )}

            <div
              className={cn(
                'max-w-2xl rounded-2xl px-6 py-4',
                message.role === 'user'
                  ? 'bg-primary-600 text-white'
                  : 'bg-white border border-gray-200'
              )}
            >
              <p className="whitespace-pre-wrap">{message.content}</p>

              {message.response && (
                <div className="mt-4 pt-4 border-t border-gray-200 space-y-2">
                  <div className="flex items-center gap-2 flex-wrap text-sm">
                    <span className={cn('badge', getConfidenceBadgeClass(message.response.confidence))}>
                      Confidence: {formatConfidence(message.response.confidence)}
                    </span>
                    <span className="badge badge-info">
                      {formatLatency(message.response.latency_ms)}
                    </span>
                    {message.response.from_cache && (
                      <span className="badge bg-purple-100 text-purple-800">Cached</span>
                    )}
                    {message.response.verification && (
                      <span
                        className={cn(
                          'badge',
                          message.response.verification.verified
                            ? 'badge-success'
                            : 'badge-warning'
                        )}
                      >
                        {message.response.verification.verified ? (
                          <>
                            <CheckCircle className="w-3 h-3 mr-1" />
                            Verified
                          </>
                        ) : (
                          <>
                            <XCircle className="w-3 h-3 mr-1" />
                            Unverified
                          </>
                        )}
                      </span>
                    )}
                  </div>

                  {message.response.citations.length > 0 && (
                    <div className="text-sm text-gray-600">
                      <p className="font-medium mb-1">Citations:</p>
                      <div className="flex flex-wrap gap-1">
                        {message.response.citations.map((citation, idx) => (
                          <span key={idx} className="badge badge-info">
                            {citation}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {message.role === 'user' && (
              <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center text-gray-700 font-semibold flex-shrink-0">
                U
              </div>
            )}
          </div>
        ))}

        {queryMutation.isPending && (
          <div className="flex gap-4 justify-start">
            <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center text-white font-semibold flex-shrink-0">
              AI
            </div>
            <div className="bg-white border border-gray-200 rounded-2xl px-6 py-4">
              <div className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-primary-600" />
                <span className="text-gray-600">Thinking...</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="bg-white border-t border-gray-200 p-6">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
          <div className="flex gap-4">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question..."
              className="input flex-1"
              disabled={queryMutation.isPending}
            />
            <button
              type="submit"
              className="btn-primary flex items-center gap-2"
              disabled={!input.trim() || queryMutation.isPending}
            >
              {queryMutation.isPending ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
              Send
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

