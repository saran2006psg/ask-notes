import React from 'react';
import { 
  Activity, 
  CheckCircle, 
  RotateCw, 
  X,
  FileText,
  Bookmark,
  Cpu,
  Database
} from 'lucide-react';

interface PipelineStatusProps {
  onClose: () => void;
  statusData: {
    status: 'idle' | 'running' | 'success' | 'failed';
    error?: string;
    ingestion?: { total_scanned: number; processed_new: number; loaded_cached: number };
    chunking?: { total_documents: number; successfully_chunked: number };
    embedding?: { total_documents: number; successfully_embedded: number };
    indexing?: { scanned_files: number; indexed_chunks: number; status: string };
  };
}

export const PipelineStatus: React.FC<PipelineStatusProps> = ({
  onClose,
  statusData
}) => {
  const steps = [
    { id: 1, label: "Document Ingestion Scan", desc: "Extracting text recursively under notes/", icon: FileText },
    { id: 2, label: "Semantic Sentence Chunking", desc: "Grouping paragraphs by similarity", icon: Bookmark },
    { id: 3, label: "Local Vector Embedding", desc: "Generating 384-dimensional features", icon: Cpu },
    { id: 4, label: "Pinecone Database Upload", desc: "Padding to 1024 dims and indexing", icon: Database }
  ];

  const getStepStatus = (stepId: number) => {
    if (statusData.status === 'failed') return 'failed';
    if (statusData.status === 'success') return 'success';
    
    // Active running logic mapping
    // We infer the active step based on missing results in sequence
    if (stepId === 1 && !statusData.ingestion) return 'running';
    if (stepId === 2 && statusData.ingestion && !statusData.chunking) return 'running';
    if (stepId === 3 && statusData.chunking && !statusData.embedding) return 'running';
    if (stepId === 4 && statusData.embedding && !statusData.indexing) return 'running';
    
    // Success check mapping
    if (stepId === 1 && statusData.ingestion) return 'success';
    if (stepId === 2 && statusData.chunking) return 'success';
    if (stepId === 3 && statusData.embedding) return 'success';
    if (stepId === 4 && statusData.indexing) return 'success';
    
    return 'pending';
  };

  return (
    <div style={{
      position: 'absolute',
      top: 0,
      left: 0,
      width: '100%',
      height: '100%',
      background: 'rgba(0,0,0,0.5)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      zIndex: 20
    }}>
      <div className="glass-panel" style={{ width: '90%', maxWidth: '520px', padding: '28px', display: 'flex', flexDirection: 'column', gap: '20px', position: 'relative' }}>
        
        {/* Close Button */}
        {(statusData.status === 'success' || statusData.status === 'failed') && (
          <button 
            onClick={onClose}
            style={{
              position: 'absolute',
              top: '20px',
              right: '20px',
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--text-muted)'
            }}
          >
            <X style={{ width: '20px' }} />
          </button>
        )}

        {/* Title Header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Activity style={{ color: 'var(--accent-cyan)', animation: statusData.status === 'running' ? 'pulse 2s infinite' : 'none' }} />
          <div>
            <h2 style={{ fontSize: '16px', fontWeight: 600 }}>RAG Ingestion & Indexing Pipeline</h2>
            <p style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>End-to-End Database Compilation Status</p>
          </div>
        </div>

        {/* Progress Stages */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {steps.map((step) => {
            const stepStatus = getStepStatus(step.id);
            const Icon = step.icon;
            
            return (
              <div 
                key={step.id} 
                className="glass-card" 
                style={{ 
                  padding: '12px 16px', 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '14px', 
                  background: stepStatus === 'running' ? 'rgba(34, 211, 238, 0.03)' : 'rgba(255,255,255,0.01)',
                  border: stepStatus === 'running' ? '1px solid rgba(34, 211, 238, 0.2)' : '1px solid var(--glass-border)'
                }}
              >
                <div style={{
                  padding: '8px',
                  borderRadius: '8px',
                  background: stepStatus === 'success' ? 'rgba(16, 185, 129, 0.08)' : stepStatus === 'running' ? 'rgba(34, 211, 238, 0.08)' : 'rgba(255,255,255,0.02)',
                  color: stepStatus === 'success' ? '#10b981' : stepStatus === 'running' ? 'var(--accent-cyan)' : 'var(--text-muted)'
                }}>
                  <Icon style={{ width: '18px', height: '18px' }} />
                </div>
                
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '13px', fontWeight: 600, color: stepStatus === 'pending' ? 'var(--text-muted)' : 'var(--text-primary)' }}>{step.label}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>{step.desc}</div>
                </div>

                <div>
                  {stepStatus === 'success' && <CheckCircle style={{ color: '#10b981', width: '20px' }} />}
                  {stepStatus === 'running' && <RotateCw style={{ color: 'var(--accent-cyan)', width: '20px', animation: 'spin 2s infinite linear' }} />}
                  {stepStatus === 'pending' && <div style={{ width: '20px', height: '20px', borderRadius: '50%', border: '2px solid var(--glass-border)' }} />}
                  {stepStatus === 'failed' && <span style={{ color: '#ef4444', fontSize: '11px', fontWeight: 600 }}>Error</span>}
                </div>
              </div>
            );
          })}
        </div>

        {/* Completion Statistics / Summary Box */}
        {statusData.status === 'success' && statusData.indexing && (
          <div className="glass-card" style={{ padding: '16px', background: 'rgba(16, 185, 129, 0.03)', border: '1px solid rgba(16, 185, 129, 0.15)', textAlign: 'center' }}>
            <h3 style={{ fontSize: '13px', fontWeight: 600, color: '#10b981', marginBottom: '4px' }}>Pipeline Ingestion Completed Successfully!</h3>
            <p style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
              We successfully scanned and indexed **{statusData.indexing.indexed_chunks} chunks** into Pinecone from your study folders.
            </p>
          </div>
        )}

        {/* Error message panel */}
        {statusData.status === 'failed' && (
          <div className="glass-card" style={{ padding: '16px', background: 'rgba(239, 68, 68, 0.03)', border: '1px solid rgba(239, 68, 68, 0.15)' }}>
            <h3 style={{ fontSize: '13px', fontWeight: 600, color: '#ef4444', marginBottom: '4px' }}>Pipeline Indexing Failed</h3>
            <p style={{ fontSize: '11px', color: 'var(--text-secondary)', wordBreak: 'break-all' }}>
              Error: {statusData.error || "Unknown pipeline error."}
            </p>
          </div>
        )}

        {/* Action button */}
        {(statusData.status === 'success' || statusData.status === 'failed') && (
          <button 
            onClick={onClose}
            className="btn-glass"
            style={{ width: '100%', padding: '10px' }}
          >
            Close Status
          </button>
        )}

        <style>{`
          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
          @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: .5; }
          }
        `}</style>
      </div>
    </div>
  );
};
