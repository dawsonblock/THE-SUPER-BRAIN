import React, { useState, useRef, useEffect } from 'react';
import { Send, Upload, Loader2, CheckCircle, XCircle, AlertCircle, Sparkles, FileText, Trash2, Settings, Brain } from 'lucide-react';
import axios from 'axios';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  confidence?: number;
  citations?: Citation[];
  cached?: boolean;
  matchType?: 'exact' | 'fuzzy';
  similarity?: number;
  processingTime?: number;
}

interface Citation {
  doc_id: string;
  chunk_id: number;
  score: number;
  text?: string;
}

interface SystemStats {
  totalDocs: number;
  cacheHitRate: number;
  avgConfidence: number;
  avgResponseTime: number;
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001';

export const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [settings, setSettings] = useState({
    enableFuzzyCache: true,
    enableVerification: true,
    confidenceThreshold: 0.70,
    fuzzyThreshold: 0.85,
    topK: 5,
    useMultiAgent: false, // Single AI by default
  });
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 30000); // Update every 30s
    return () => clearInterval(interval);
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API_URL}/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await axios.post(`${API_URL}/answer`, {
        question: input,
        top_k: settings.topK,
        enable_verification: settings.enableVerification,
        enable_fuzzy_cache: settings.enableFuzzyCache,
        confidence_threshold: settings.confidenceThreshold,
        fuzzy_threshold: settings.fuzzyThreshold,
        use_multi_agent: settings.useMultiAgent, // Deep Think mode
      });

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.data.answer,
        timestamp: new Date(),
        confidence: response.data.confidence,
        citations: response.data.citations,
        cached: response.data.cached,
        matchType: response.data.match_type,
        similarity: response.data.similarity,
        processingTime: response.data.processing_time_ms,
      };

      setMessages(prev => [...prev, assistantMessage]);
      fetchStats(); // Update stats after query
    } catch (error: any) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Error: ${error.response?.data?.detail || error.message || 'Failed to get response'}`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    setUploadProgress(0);

    try {
      const formData = new FormData();
      Array.from(files).forEach(file => {
        formData.append('files', file);
      });

      await axios.post(`${API_URL}/documents/batch`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const progress = progressEvent.total
            ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
            : 0;
          setUploadProgress(progress);
        },
      });

      const successMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `✅ Successfully uploaded ${files.length} document(s)! They are now indexed and ready for search.`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, successMessage]);
      fetchStats(); // Update stats after upload
    } catch (error: any) {
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `❌ Upload failed: ${error.response?.data?.detail || error.message}`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setUploadProgress(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleClearChat = () => {
    if (window.confirm('Clear all messages?')) {
      setMessages([]);
    }
  };

  const getConfidenceColor = (confidence?: number) => {
    if (!confidence) return 'text-gray-400';
    if (confidence >= 0.85) return 'text-green-500';
    if (confidence >= 0.70) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getConfidenceIcon = (confidence?: number) => {
    if (!confidence) return null;
    if (confidence >= 0.85) return <CheckCircle className="w-4 h-4" />;
    if (confidence >= 0.70) return <AlertCircle className="w-4 h-4" />;
    return <XCircle className="w-4 h-4" />;
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-gradient-to-br from-blue-500 to-purple-600 p-2 rounded-lg">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                  Brain-AI
                </h1>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  RAG++ Cognitive System v4.5.0
                </p>
              </div>
            </div>
            
            {/* Stats */}
            {stats && (
              <div className="hidden md:flex items-center space-x-6 text-sm">
                <div className="text-center">
                  <div className="text-gray-500 dark:text-gray-400">Documents</div>
                  <div className="font-semibold text-gray-900 dark:text-white">
                    {stats.totalDocs}
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-gray-500 dark:text-gray-400">Cache Hit</div>
                  <div className="font-semibold text-green-600 dark:text-green-400">
                    {(stats.cacheHitRate * 100).toFixed(0)}%
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-gray-500 dark:text-gray-400">Avg Time</div>
                  <div className="font-semibold text-blue-600 dark:text-blue-400">
                    {stats.avgResponseTime.toFixed(0)}ms
                  </div>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex items-center space-x-2">
              {/* Deep Think Toggle */}
              <button
                onClick={() => setSettings(prev => ({ ...prev, useMultiAgent: !prev.useMultiAgent }))}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-all ${
                  settings.useMultiAgent
                    ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
                title={settings.useMultiAgent ? 'Deep Think Mode: ON (Multi-Agent)' : 'Deep Think Mode: OFF (Single AI)'}
              >
                <Brain className="w-5 h-5" />
                <span className="hidden sm:inline">
                  {settings.useMultiAgent ? 'Deep Think' : 'Fast Mode'}
                </span>
              </button>
              
              <button
                onClick={() => fileInputRef.current?.click()}
                className="p-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                title="Upload documents"
              >
                <Upload className="w-5 h-5" />
              </button>
              <button
                onClick={() => setShowSettings(!showSettings)}
                className="p-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                title="Settings"
              >
                <Settings className="w-5 h-5" />
              </button>
              <button
                onClick={handleClearChat}
                className="p-2 text-gray-600 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                title="Clear chat"
              >
                <Trash2 className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Settings Panel */}
      {showSettings && (
        <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Query Settings
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="flex items-center space-x-2 text-sm text-gray-700 dark:text-gray-300">
                  <input
                    type="checkbox"
                    checked={settings.useMultiAgent}
                    onChange={(e) => setSettings({ ...settings, useMultiAgent: e.target.checked })}
                    className="rounded"
                  />
                  <span className="flex items-center space-x-1">
                    <Brain className="w-4 h-4" />
                    <span>Deep Think Mode (Multi-Agent)</span>
                  </span>
                </label>
              </div>
              <div>
                <label className="flex items-center space-x-2 text-sm text-gray-700 dark:text-gray-300">
                  <input
                    type="checkbox"
                    checked={settings.enableFuzzyCache}
                    onChange={(e) => setSettings({ ...settings, enableFuzzyCache: e.target.checked })}
                    className="rounded"
                  />
                  <span>Enable Fuzzy Cache (50-80% better hits!)</span>
                </label>
              </div>
              <div>
                <label className="flex items-center space-x-2 text-sm text-gray-700 dark:text-gray-300">
                  <input
                    type="checkbox"
                    checked={settings.enableVerification}
                    onChange={(e) => setSettings({ ...settings, enableVerification: e.target.checked })}
                    className="rounded"
                  />
                  <span>Enable Verification</span>
                </label>
              </div>
              <div>
                <label className="block text-sm text-gray-700 dark:text-gray-300 mb-1">
                  Confidence Threshold: {settings.confidenceThreshold.toFixed(2)}
                </label>
                <input
                  type="range"
                  min="0.5"
                  max="0.95"
                  step="0.05"
                  value={settings.confidenceThreshold}
                  onChange={(e) => setSettings({ ...settings, confidenceThreshold: parseFloat(e.target.value) })}
                  className="w-full"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-700 dark:text-gray-300 mb-1">
                  Fuzzy Threshold: {settings.fuzzyThreshold.toFixed(2)}
                </label>
                <input
                  type="range"
                  min="0.70"
                  max="0.95"
                  step="0.05"
                  value={settings.fuzzyThreshold}
                  onChange={(e) => setSettings({ ...settings, fuzzyThreshold: parseFloat(e.target.value) })}
                  className="w-full"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-700 dark:text-gray-300 mb-1">
                  Top K Results: {settings.topK}
                </label>
                <input
                  type="range"
                  min="1"
                  max="10"
                  step="1"
                  value={settings.topK}
                  onChange={(e) => setSettings({ ...settings, topK: parseInt(e.target.value) })}
                  className="w-full"
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <div className="bg-gradient-to-br from-blue-500 to-purple-600 p-4 rounded-full inline-block mb-4">
                <Sparkles className="w-12 h-12 text-white" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                Welcome to Brain-AI
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Ask me anything about your documents!
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto">
                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
                  <FileText className="w-6 h-6 text-blue-500 mb-2" />
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                    Upload Documents
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    PDFs, images, and text files supported
                  </p>
                </div>
                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
                  <Sparkles className="w-6 h-6 text-purple-500 mb-2" />
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                    Smart Caching
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Fuzzy matching for 50-80% better cache hits!
                  </p>
                </div>
              </div>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-3xl rounded-2xl px-6 py-4 ${
                  message.role === 'user'
                    ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white'
                    : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm'
                }`}
              >
                <div className="flex items-start space-x-3">
                  {message.role === 'assistant' && (
                    <div className="bg-gradient-to-br from-purple-500 to-purple-600 p-2 rounded-lg flex-shrink-0">
                      <Sparkles className="w-4 h-4 text-white" />
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm whitespace-pre-wrap break-words ${
                      message.role === 'user' ? 'text-white' : 'text-gray-900 dark:text-white'
                    }`}>
                      {message.content}
                    </p>

                    {/* Metadata */}
                    {message.role === 'assistant' && (
                      <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700 space-y-2">
                        {/* Confidence */}
                        {message.confidence !== undefined && (
                          <div className="flex items-center space-x-2 text-xs">
                            <span className={`flex items-center space-x-1 ${getConfidenceColor(message.confidence)}`}>
                              {getConfidenceIcon(message.confidence)}
                              <span>Confidence: {(message.confidence * 100).toFixed(0)}%</span>
                            </span>
                          </div>
                        )}

                        {/* Cache Status */}
                        {message.cached && (
                          <div className="flex items-center space-x-2 text-xs text-green-600 dark:text-green-400">
                            <CheckCircle className="w-3 h-3" />
                            <span>
                              Cached ({message.matchType === 'fuzzy' ? `Fuzzy ${(message.similarity! * 100).toFixed(0)}%` : 'Exact'})
                            </span>
                          </div>
                        )}

                        {/* Processing Time */}
                        {message.processingTime && (
                          <div className="text-xs text-gray-500 dark:text-gray-400">
                            Response time: {message.processingTime}ms
                          </div>
                        )}

                        {/* Citations */}
                        {message.citations && message.citations.length > 0 && (
                          <div className="mt-2">
                            <div className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                              Sources:
                            </div>
                            <div className="space-y-1">
                              {message.citations.slice(0, 3).map((citation, idx) => (
                                <div
                                  key={idx}
                                  className="text-xs bg-gray-50 dark:bg-gray-700 px-2 py-1 rounded"
                                >
                                  <span className="font-mono text-gray-600 dark:text-gray-400">
                                    {citation.doc_id}
                                  </span>
                                  <span className="text-gray-500 dark:text-gray-500 mx-1">•</span>
                                  <span className="text-gray-600 dark:text-gray-400">
                                    Chunk {citation.chunk_id}
                                  </span>
                                  <span className="text-gray-500 dark:text-gray-500 mx-1">•</span>
                                  <span className="text-blue-600 dark:text-blue-400">
                                    {(citation.score * 100).toFixed(0)}%
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Timestamp */}
                    <div className={`mt-2 text-xs ${
                      message.role === 'user' ? 'text-blue-100' : 'text-gray-500 dark:text-gray-400'
                    }`}>
                      {message.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}

          {/* Loading indicator */}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl px-6 py-4 shadow-sm">
                <div className="flex items-center space-x-3">
                  <div className="bg-gradient-to-br from-purple-500 to-purple-600 p-2 rounded-lg">
                    <Sparkles className="w-4 h-4 text-white" />
                  </div>
                  <div className="flex items-center space-x-2 text-gray-600 dark:text-gray-400">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span className="text-sm">Thinking...</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Upload progress */}
          {uploadProgress !== null && (
            <div className="flex justify-start">
              <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl px-6 py-4 shadow-sm max-w-md">
                <div className="flex items-center space-x-3 mb-2">
                  <Upload className="w-5 h-5 text-blue-500" />
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    Uploading documents...
                  </span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mt-1 text-right">
                  {uploadProgress}%
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 shadow-lg">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-end space-x-3">
            <div className="flex-1">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                placeholder="Ask me anything about your documents..."
                rows={1}
                className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
                style={{ minHeight: '48px', maxHeight: '200px' }}
              />
            </div>
            <button
              onClick={handleSendMessage}
              disabled={!input.trim() || isLoading}
              className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 text-white rounded-xl hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-xl"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>
          <div className="mt-2 text-xs text-gray-500 dark:text-gray-400 text-center">
            Press Enter to send • Shift+Enter for new line
          </div>
        </div>
      </div>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".pdf,.png,.jpg,.jpeg,.txt,.md"
        onChange={handleFileUpload}
        className="hidden"
      />
    </div>
  );
};

export default ChatInterface;
