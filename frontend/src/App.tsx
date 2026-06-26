import { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { ChatContainer } from './components/ChatContainer';
import { PipelineStatus } from './components/PipelineStatus';
import './App.css';

interface Citation {
  filename: string;
  subject: string;
  page: number;
  source: string;
  chunk_id: string;
  score: number;
  text?: string;
}

interface ChatImage {
  path: string;
  description: string;
  url: string;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  images?: ChatImage[];
}

interface PipelineData {
  status: 'idle' | 'running' | 'success' | 'failed';
  error?: string;
  ingestion?: { total_scanned: number; processed_new: number; loaded_cached: number };
  chunking?: { total_documents: number; successfully_chunked: number };
  embedding?: { total_documents: number; successfully_embedded: number };
  indexing?: { scanned_files: number; indexed_chunks: number; status: string };
}

function NotesAppContent() {
  const [activeSubject, setActiveSubject] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [showPipeline, setShowPipeline] = useState<boolean>(false);
  const [pipelineStatus, setPipelineStatus] = useState<PipelineData>({ status: 'idle' });
  const [stats, setStats] = useState({
    totalDocs: 0,
    totalPages: 0,
    totalChunks: 0
  });

  const fetchWithAuth = async (url: string, options: RequestInit = {}) => {
    return fetch(url, options);
  };

  // Fetch db stats
  const fetchStats = async () => {
    try {
      const res = await fetchWithAuth("/api/vectorstore/stats");
      const analysisRes = await fetchWithAuth("/api/documents/analysis");
      
      let docCount = 0;
      let pageCount = 0;
      let chunkCount = 0;

      if (analysisRes.ok) {
        const analysisData = await analysisRes.json();
        docCount = analysisData.overall?.total_documents || 0;
        pageCount = analysisData.overall?.total_pages || 0;
      }
      
      if (res.ok) {
        const statsData = await res.json();
        chunkCount = statsData.total_chunks || 0;
      }

      setStats({
        totalDocs: docCount,
        totalPages: pageCount,
        totalChunks: chunkCount
      });
    } catch (e) {
      console.error("Failed to load statistics", e);
    }
  };

  useEffect(() => {
    fetchStats();
    // Poll stats every 15 seconds
    const interval = setInterval(fetchStats, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleSendMessage = async (text: string) => {
    // 1. Add user message
    const userMsg: Message = { role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    try {
      // 2. Query FastAPI Chat Route
      const res = await fetchWithAuth("/api/chat", {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: text,
          subject: activeSubject,
          top_k: 4,
          rerank: true
        })
      });

      if (res.ok) {
        const data = await res.json();
        
        // Match verified citation bodies against their texts in retrieved results
        const enrichedCitations = (data.verified_citations || []).map((cit: Citation) => {
          const matchingRetrieved = (data.retrieved_citations || []).find((ret: any) => ret.chunk_id === cit.chunk_id);
          return {
            ...cit,
            text: matchingRetrieved ? matchingRetrieved.text : (cit.text || "")
          };
        });

        const assistantMsg: Message = {
          role: 'assistant',
          content: data.answer,
          citations: enrichedCitations,
          images: data.images || []
        };
        
        setMessages(prev => [...prev, assistantMsg]);
      } else {
        const errData = await res.json();
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `Error: ${errData.detail || "Unable to complete chat request."}`
        }]);
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: "Error: Network connection failed. Please ensure the backend is running."
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTriggerPipeline = async () => {
    setShowPipeline(true);
    setPipelineStatus({ status: 'running' });

    try {
      const res = await fetchWithAuth("/api/pipeline/run", {
        method: 'POST'
      });
      const data = await res.json();

      if (res.ok) {
        setPipelineStatus({
          status: 'success',
          ingestion: data.ingestion,
          chunking: data.chunking,
          embedding: data.embedding,
          indexing: data.indexing
        });
        fetchStats();
      } else {
        setPipelineStatus({
          status: 'failed',
          error: data.detail || "Unified pipeline indexing run failed."
        });
      }
    } catch (err) {
      setPipelineStatus({
        status: 'failed',
        error: "Network connection error occurred while running the pipeline."
      });
    }
  };

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw', padding: '16px', gap: '16px', boxSizing: 'border-box', overflow: 'hidden' }}>
      
      {/* Sidebar selection & uploader */}
      <Sidebar 
        activeSubject={activeSubject}
        setActiveSubject={setActiveSubject}
        stats={stats}
        triggerPipeline={handleTriggerPipeline}
        isPipelineRunning={pipelineStatus.status === 'running'}
      />

      {/* Main chat interface panel */}
      <div className="glass-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
        <ChatContainer 
          messages={messages}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          activeSubject={activeSubject}
        />
      </div>

      {/* Indexing pipeline overlay modal */}
      {showPipeline && (
        <PipelineStatus 
          onClose={() => {
            setShowPipeline(false);
            setPipelineStatus({ status: 'idle' });
          }}
          statusData={pipelineStatus}
        />
      )}
    </div>
  );
}

function App() {
  return (
    <>
      <NotesAppContent />
    </>
  );
}

export default App;
