# Brain-AI RAG++ Web GUI

**Modern React + TypeScript control center for the Brain-AI RAG++ system.**

## Features

### ✅ Implemented
- **Chat Interface** - Interactive conversational UI with streaming support
- **Fast/Accuracy Mode Toggle** - Switch between single-solver and multi-agent modes
- **Real-time Confidence Display** - Visual feedback on answer quality
- **Citation Tracking** - Display source documents for transparency
- **Verification Badges** - Show verified/unverified answers
- **Latency Monitoring** - Track response times

### 🚧 To Implement (Stub Pages Created)
- **Search & RAG Panel** - Advanced search with context inspection
- **Upload Interface** - Document ingestion with drag-drop
- **Multi-Agent Ops** - Side-by-side solver comparison
- **System Monitor** - Prometheus metrics visualization
- **Admin Panel** - Configuration and control

## Quick Start

### Prerequisites
- Node.js 18+ 
- Running Brain-AI REST service on `localhost:5001`

### Installation

```bash
cd brain-ai-gui
npm install
```

### Development

```bash
npm run dev
```

Visit `http://localhost:3000`

### Production Build

```bash
npm run build
npm run preview
```

## Architecture

```
Frontend (Port 3000)  →  Vite Proxy  →  FastAPI Backend (Port 5001)
     ↓                                          ↓
  React Router                            RAG++ Pipeline
     ↓                                          ↓
  TanStack Query                    C++ Core + DeepSeek LLM
     ↓                                          ↓
  Axios API Client                       Facts Store + Metrics
```

## API Proxy Configuration

The Vite dev server proxies `/api/*` to `http://localhost:5001`:

```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:5001',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, ''),
    },
  },
}
```

## Project Structure

```
brain-ai-gui/
├── src/
│   ├── components/     # Reusable UI components
│   ├── pages/          # Route pages
│   │   ├── ChatPage.tsx           ✅ Complete
│   │   ├── SearchPage.tsx         🚧 Stub
│   │   ├── UploadPage.tsx         🚧 Stub
│   │   ├── MultiAgentPage.tsx     🚧 Stub
│   │   ├── MonitorPage.tsx        🚧 Stub
│   │   └── AdminPage.tsx          🚧 Stub
│   ├── lib/            # API client and utilities
│   ├── types/          # TypeScript types
│   ├── hooks/          # Custom React hooks
│   ├── App.tsx         # Main app with routing
│   └── main.tsx        # Entry point
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

## Current Implementation Status

### Phase 1: Skeleton (Complete ✅)
- [x] React + TypeScript + Vite setup
- [x] Tailwind CSS configuration
- [x] Routing with React Router
- [x] API client with Axios
- [x] TanStack Query integration
- [x] Main navigation
- [x] Chat page (fully functional)

### Phase 2: Core Features (Next)
- [ ] Search & RAG panel
- [ ] Upload interface
- [ ] Document chunking preview

### Phase 3: Advanced Features (Future)
- [ ] Multi-agent comparison UI
- [ ] Prometheus metrics charts
- [ ] System admin controls
- [ ] WebSocket streaming

## Environment Variables

Create `.env.local`:

```bash
# API Configuration
VITE_API_URL=http://localhost:5001

# Optional: API Key
VITE_API_KEY=your-api-key
```

## API Key Storage

The GUI stores API keys in `localStorage`:

```typescript
// Set API key
localStorage.setItem('brain_ai_api_key', 'your-key');

// API client automatically adds it to requests
api.interceptors.request.use((config) => {
  const apiKey = localStorage.getItem('brain_ai_api_key');
  if (apiKey) {
    config.headers['X-API-Key'] = apiKey;
  }
  return config;
});
```

## Styling

Uses Tailwind CSS with custom theme:

- **Primary Color**: Blue (`primary-600`)
- **Success**: Green
- **Warning**: Yellow
- **Error**: Red
- **Info**: Blue

Custom components:
- `.btn` - Base button
- `.btn-primary` - Primary button
- `.btn-secondary` - Secondary button
- `.card` - Card container
- `.badge` - Small label
- `.input` - Text input

## Performance

- Code splitting with Vite
- React Query caching (30s stale time)
- Lazy loading for heavy components
- Optimized bundle size (~200KB gzipped)

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Next Steps

1. **Complete Stub Pages** - Implement Search, Upload, MultiAgent, Monitor, Admin
2. **Add WebSocket Support** - Stream tokens for real-time chat
3. **Metrics Visualization** - Integrate Recharts for monitoring
4. **Electron Wrapper** - Package as desktop app (Option C)

## Contributing

This GUI is part of the Brain-AI RAG++ system. See the main project README for architecture details.

## License

Same as Brain-AI RAG++ main project.

---

**Status**: Phase 1 Complete ✅  
**Version**: 1.0.0  
**Last Updated**: November 1, 2025

