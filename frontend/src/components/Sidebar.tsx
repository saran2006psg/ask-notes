import React, { useState, useEffect } from 'react';
import { 
  BookOpen, 
  UploadCloud, 
  Folder, 
  Layers, 
  FileText, 
  Activity,
  CheckCircle,
  AlertCircle
} from 'lucide-react';

interface SidebarProps {
  activeSubject: string | null;
  setActiveSubject: (subject: string | null) => void;
  stats: {
    totalDocs: number;
    totalPages: number;
    totalChunks: number;
  };
  triggerPipeline: () => void;
  isPipelineRunning: boolean;
}

interface IngestedDoc {
  filename: string;
  subject: string;
  format: string;
  file_size_bytes: number;
  is_processed: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeSubject,
  setActiveSubject,
  stats,
  triggerPipeline,
  isPipelineRunning
}) => {
  const [documents, setDocuments] = useState<IngestedDoc[]>([]);
  const [uploadSubject, setUploadSubject] = useState<string>("data_privacy_and_security");
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);
  const [uploadStatus, setUploadStatus] = useState<{ type: 'success' | 'error' | null; message: string }>({ type: null, message: "" });
  const [isUploading, setIsUploading] = useState<boolean>(false);

  const subjects = [
    { id: null, name: "All Subjects", count: 0 },
    { id: "data_privacy_and_security", name: "Data Privacy & Sec.", count: 0 },
    { id: "DBMS", name: "DBMS", count: 0 },
    { id: "Operating Systems", name: "Operating Systems", count: 0 },
    { id: "Computer Networks", name: "Computer Networks", count: 0 },
    { id: "OOP", name: "OOP", count: 0 }
  ];

  // Fetch document lists
  const fetchDocuments = async () => {
    try {
      const res = await fetch("/api/documents");
      if (res.ok) {
        const data = await res.json();
        setDocuments(data.documents || []);
      }
    } catch (e) {
      console.error("Failed to fetch documents", e);
    }
  };

  useEffect(() => {
    fetchDocuments();
    // Poll documents list every 10 seconds to detect new items
    const interval = setInterval(fetchDocuments, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setSelectedFiles(e.target.files);
      setUploadStatus({ type: null, message: "" });
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFiles || selectedFiles.length === 0) return;

    setIsUploading(true);
    setUploadStatus({ type: null, message: "" });

    const formData = new FormData();
    for (let i = 0; i < selectedFiles.length; i++) {
      formData.append("files", selectedFiles[i]);
    }

    try {
      const url = `/api/ingest/upload?subject=${encodeURIComponent(uploadSubject)}`;
      const res = await fetch(url, {
        method: 'POST',
        body: formData
      });

      const data = await res.json();
      if (res.ok) {
        setUploadStatus({
          type: 'success',
          message: `Successfully uploaded ${data.total_uploaded} file(s)!`
        });
        setSelectedFiles(null);
        // Reset file input element
        const fileInput = document.getElementById("file-input-field") as HTMLInputElement;
        if (fileInput) fileInput.value = "";
        fetchDocuments();
      } else {
        setUploadStatus({
          type: 'error',
          message: data.detail || "Failed to upload files."
        });
      }
    } catch (err) {
      setUploadStatus({
        type: 'error',
        message: "Network error occurred."
      });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="glass-panel" style={{ width: 'var(--sidebar-width)', height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      
      {/* App Header */}
      <div style={{ padding: '24px 20px', borderBottom: '1px solid var(--glass-border)', display: 'flex', alignItems: 'center', gap: '12px' }}>
        <BookOpen style={{ color: 'var(--accent-cyan)', width: '28px', height: '28px' }} />
        <div>
          <h1 style={{ fontSize: '18px', fontWeight: 700, letterSpacing: '-0.5px' }}>Easy Study</h1>
          <p style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>College Notes RAG Assistant</p>
        </div>
      </div>

      {/* Stats Widget */}
      <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--glass-border)', display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)' }}>
          <Activity style={{ width: '14px', height: '14px' }} />
          <span>KNOWLEDGE BASE STATS</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
          <div className="glass-card" style={{ padding: '8px', textAlign: 'center', background: 'rgba(255, 255, 255, 0.015)' }}>
            <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--accent-cyan)' }}>{stats.totalDocs}</div>
            <div style={{ fontSize: '9px', color: 'var(--text-muted)', marginTop: '2px' }}>Files</div>
          </div>
          <div className="glass-card" style={{ padding: '8px', textAlign: 'center', background: 'rgba(255, 255, 255, 0.015)' }}>
            <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--accent-purple)' }}>{stats.totalPages}</div>
            <div style={{ fontSize: '9px', color: 'var(--text-muted)', marginTop: '2px' }}>Pages</div>
          </div>
          <div className="glass-card" style={{ padding: '8px', textAlign: 'center', background: 'rgba(255, 255, 255, 0.015)' }}>
            <div style={{ fontSize: '16px', fontWeight: 700, color: '#f59e0b' }}>{stats.totalChunks}</div>
            <div style={{ fontSize: '9px', color: 'var(--text-muted)', marginTop: '2px' }}>Chunks</div>
          </div>
        </div>
      </div>

      {/* Uploader Section */}
      <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--glass-border)' }}>
        <form onSubmit={handleUpload} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ display: 'flex', gap: '8px' }}>
            <select
              value={uploadSubject}
              onChange={(e) => setUploadSubject(e.target.value)}
              className="input-glass"
              style={{ flex: 1, padding: '8px', fontSize: '12px', background: '#0e1017' }}
            >
              <option value="data_privacy_and_security">Data Privacy</option>
              <option value="DBMS">DBMS</option>
              <option value="Operating Systems">OS</option>
              <option value="Computer Networks">Networks</option>
              <option value="OOP">OOP</option>
            </select>
            <button
              type="button"
              onClick={triggerPipeline}
              disabled={isPipelineRunning}
              className="btn-glass btn-primary"
              style={{ padding: '8px 12px', fontSize: '11px', display: 'flex', alignItems: 'center', gap: '4px' }}
            >
              <Layers style={{ width: '13px', height: '13px' }} />
              {isPipelineRunning ? "Indexing..." : "Index DB"}
            </button>
          </div>
          <div style={{ position: 'relative', display: 'flex', flexDirection: 'column' }}>
            <label 
              htmlFor="file-input-field" 
              className="glass-panel-interactive" 
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                padding: '16px 12px',
                border: '1px dashed var(--glass-border)',
                borderRadius: '8px',
                cursor: 'pointer',
                textAlign: 'center'
              }}
            >
              <UploadCloud style={{ color: 'var(--accent-cyan)', width: '22px', height: '22px', marginBottom: '6px' }} />
              <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                {selectedFiles ? `${selectedFiles.length} file(s) selected` : "Select PDF/PPTX/DOCX"}
              </span>
            </label>
            <input 
              type="file" 
              id="file-input-field" 
              multiple 
              accept=".pdf,.pptx,.docx" 
              onChange={handleFileChange}
              style={{ display: 'none' }}
            />
          </div>
          {selectedFiles && (
            <button
              type="submit"
              disabled={isUploading}
              className="btn-glass"
              style={{ width: '100%', padding: '8px', fontSize: '12px', background: 'rgba(255,255,255,0.06)' }}
            >
              {isUploading ? "Uploading..." : "Upload Files"}
            </button>
          )}
          {uploadStatus.type && (
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '6px', 
              fontSize: '11px', 
              color: uploadStatus.type === 'success' ? '#10b981' : '#ef4444',
              marginTop: '4px' 
            }}>
              {uploadStatus.type === 'success' ? <CheckCircle style={{ width: '14px' }} /> : <AlertCircle style={{ width: '14px' }} />}
              <span>{uploadStatus.message}</span>
            </div>
          )}
        </form>
      </div>

      {/* Subject Filter list */}
      <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--glass-border)', flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '10px' }}>
          <Folder style={{ width: '14px', height: '14px' }} />
          <span>FILTER BY SUBJECT</span>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', overflowY: 'auto', paddingRight: '4px' }}>
          {subjects.map((sub) => {
            const isSelected = activeSubject === sub.id;
            return (
              <button
                key={sub.id || "all"}
                onClick={() => setActiveSubject(sub.id)}
                className="glass-panel-interactive"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: '10px 12px',
                  borderRadius: '8px',
                  border: isSelected ? '1px solid var(--accent-cyan)' : '1px solid transparent',
                  background: isSelected ? 'rgba(34, 211, 238, 0.08)' : 'rgba(255,255,255,0.01)',
                  color: isSelected ? 'var(--text-primary)' : 'var(--text-secondary)',
                  cursor: 'pointer',
                  textAlign: 'left',
                  width: '100%',
                  fontSize: '12.5px',
                  fontWeight: isSelected ? 600 : 400
                }}
              >
                <div style={{ 
                  width: '6px', 
                  height: '6px', 
                  borderRadius: '50%', 
                  background: sub.id ? 'var(--accent-purple)' : 'var(--accent-cyan)',
                  marginRight: '10px' 
                }} />
                <span style={{ flex: 1 }}>{sub.name}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Documents List panel */}
      <div style={{ padding: '16px 20px', background: 'rgba(0,0,0,0.1)', height: '160px', display: 'flex', flexDirection: 'column' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '8px' }}>
          <FileText style={{ width: '13px', height: '13px' }} />
          <span>INGESTED DOCUMENTS ({documents.length})</span>
        </div>
        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '6px', paddingRight: '4px' }}>
          {documents.length === 0 ? (
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', padding: '10px 0' }}>No documents uploaded yet.</div>
          ) : (
            documents.map((doc, idx) => (
              <div 
                key={idx} 
                className="glass-card" 
                style={{ 
                  padding: '8px 10px', 
                  fontSize: '11px', 
                  background: 'rgba(255,255,255,0.01)', 
                  display: 'flex', 
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}
              >
                <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '180px', color: 'var(--text-secondary)' }}>
                  {doc.filename}
                </div>
                <div style={{ 
                  fontSize: '9px', 
                  color: 'var(--accent-cyan)',
                  background: 'rgba(34, 211, 238, 0.08)',
                  padding: '1px 5px',
                  borderRadius: '4px'
                }}>
                  {doc.subject.substring(0, 8)}...
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
