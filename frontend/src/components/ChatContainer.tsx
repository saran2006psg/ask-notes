import React, { useState, useRef, useEffect } from 'react';
import { Send, FileText, Bookmark, CheckCircle2, ChevronRight, X } from 'lucide-react';

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

interface ChatMessageBubbleProps {
  msg: Message;
  isUser: boolean;
  onCitationClick: (cit: Citation) => void;
  onImageClick: (img: ChatImage) => void;
  formatMessageContent: (content: string) => string;
}

const ChatMessageBubble: React.FC<ChatMessageBubbleProps> = ({
  msg,
  isUser,
  onCitationClick,
  onImageClick,
  formatMessageContent
}) => {
  const [showCitations, setShowCitations] = useState(false);
  
  return (
    <div 
      style={{ 
        display: 'flex', 
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        width: '100%' 
      }}
    >
      <div 
        className="glass-card"
        style={{ 
          padding: '16px 20px', 
          maxWidth: '85%', 
          background: isUser ? 'rgba(244, 63, 94, 0.08)' : 'var(--glass-bg)',
          border: isUser ? '1px solid rgba(244, 63, 94, 0.18)' : '1px solid var(--glass-border)'
        }}
      >
        <div style={{ 
          fontSize: '10px', 
          fontWeight: 600, 
          color: isUser ? 'var(--accent-purple)' : 'var(--accent-cyan)',
          marginBottom: '6px',
          letterSpacing: '0.5px' 
        }}>
          {isUser ? "STUDENT" : "STUDY ASSISTANT"}
        </div>
        
        {/* Content render */}
        <div style={{ 
          fontSize: '13.5px', 
          lineHeight: '1.6', 
          color: 'var(--text-primary)',
          whiteSpace: 'pre-wrap' 
        }}>
          {isUser ? msg.content : formatMessageContent(msg.content)}
        </div>

        {/* Render images if any */}
        {!isUser && msg.images && msg.images.length > 0 && (
          <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {msg.images.map((img, idx) => (
              <div 
                key={idx} 
                className="glass-card" 
                style={{ 
                  padding: '8px', 
                  background: 'rgba(0,0,0,0.2)',
                  cursor: 'pointer',
                  border: '1px solid rgba(255,255,255,0.05)',
                  transition: 'border-color 0.2s',
                }}
                onClick={() => onImageClick(img)}
                onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--accent-cyan)')}
                onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'rgba(255,255,255,0.05)')}
              >
                <img 
                  src={img.url} 
                  alt="Extracted context" 
                  style={{ width: '100%', maxHeight: '200px', objectFit: 'contain', borderRadius: '4px' }}
                />
                {img.description && (
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '8px', fontStyle: 'italic' }}>
                    {img.description}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Render verified inline citations list */}
        {!isUser && msg.citations && msg.citations.length > 0 && (
          <div style={{ marginTop: '16px', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '12px' }}>
            <button
              onClick={() => setShowCitations(!showCitations)}
              className="glass-panel-interactive"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                padding: '6px 12px',
                borderRadius: '20px',
                background: showCitations ? 'rgba(244, 63, 94, 0.08)' : 'rgba(0, 0, 0, 0.02)',
                border: showCitations ? '1px solid rgba(244, 63, 94, 0.18)' : '1px solid var(--glass-border)',
                fontSize: '11px',
                color: showCitations ? 'var(--accent-purple)' : 'var(--text-secondary)',
                cursor: 'pointer',
                gap: '6px',
                transition: 'all 0.2s ease',
                fontWeight: 600
              }}
            >
              <FileText style={{ width: '13px', height: '13px', color: 'var(--accent-cyan)' }} />
              <span>{showCitations ? "Hide Citations" : "Show Citations"} ({msg.citations.length})</span>
              <span style={{ fontSize: '9px', opacity: 0.7 }}>
                {showCitations ? "▲" : "▼"}
              </span>
            </button>
            
            {showCitations && (
              <div 
                className="fade-in"
                style={{ 
                  marginTop: '12px', 
                  display: 'flex', 
                  flexDirection: 'column',
                  gap: '8px'
                }}
              >
                <div style={{ fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '2px', letterSpacing: '0.5px' }}>
                  VERIFIED SOURCES:
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {msg.citations.map((cit, cIdx) => (
                    <button
                      key={cIdx}
                      onClick={() => onCitationClick(cit)}
                      className="glass-panel-interactive"
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        padding: '6px 12px',
                        borderRadius: '8px',
                        background: 'rgba(255,255,255,0.02)',
                        border: '1px solid var(--glass-border)',
                        fontSize: '11px',
                        color: 'var(--text-secondary)',
                        cursor: 'pointer',
                        gap: '6px',
                        transition: 'all 0.2s ease'
                      }}
                    >
                      <CheckCircle2 style={{ width: '12px', height: '12px', color: '#10b981' }} />
                      <span style={{ fontWeight: 500 }}>{cit.filename}</span>
                      <span style={{ color: 'var(--text-muted)' }}>| Page {cit.page}</span>
                      <ChevronRight style={{ width: '12px', height: '12px', color: 'var(--text-muted)', marginLeft: '4px' }} />
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

interface ChatContainerProps {
  messages: Message[];
  onSendMessage: (text: string) => void;
  isLoading: boolean;
  activeSubject: string | null;
}

export const ChatContainer: React.FC<ChatContainerProps> = ({
  messages,
  onSendMessage,
  isLoading,
  activeSubject
}) => {
  const [input, setInput] = useState<string>("");
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [selectedImage, setSelectedImage] = useState<ChatImage | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSendMessage(input.trim());
    setInput("");
  };

  const handleCitationClick = (citation: Citation) => {
    setSelectedCitation(citation);
  };

  const formatMessageContent = (content: string) => {
    // Strip parenthetical citations like (Source: filename - Page 12) or variations
    let cleaned = content.replace(/\s*\(Source:\s*.*?-\s*Page\s*\d+\)/gi, "");
    // Clean up any periods with spaces before them
    cleaned = cleaned.replace(/\s+\./g, ".").replace(/\s+,/g, ",");
    return cleaned.trim();
  };

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden', position: 'relative' }}>
      
      {/* Subject Filter Indicator Header */}
      <div style={{ padding: '16px 24px', borderBottom: '1px solid var(--glass-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ 
            width: '8px', 
            height: '8px', 
            borderRadius: '50%', 
            background: activeSubject ? 'var(--accent-purple)' : 'var(--accent-cyan)' 
          }} />
          <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)' }}>
            {activeSubject ? `Active Filter: ${activeSubject}` : "Searching All Notes"}
          </span>
        </div>
        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
          Groq Inference: Llama-3.1-8b-instant
        </div>
      </div>

      {/* Message History list */}
      <div 
        ref={scrollRef}
        style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}
      >
        {messages.length === 0 ? (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', textAlign: 'center', padding: '40px' }}>
            <div className="glass-panel" style={{ padding: '24px', maxWidth: '440px', background: 'rgba(255,255,255,0.01)' }}>
              <Bookmark style={{ color: 'var(--accent-cyan)', width: '36px', height: '36px', marginBottom: '12px' }} />
              <h2 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '6px' }}>Ready to Assist!</h2>
              <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                Ask any question about your loaded study notes (DBMS, OS, Networks, OOP, or Data Privacy). 
                The RAG pipeline will retrieve matches, rerank using BGE, and synthesize answers with verified citations.
              </p>
            </div>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <ChatMessageBubble
              key={idx}
              msg={msg}
              isUser={msg.role === 'user'}
              onCitationClick={handleCitationClick}
              onImageClick={(img) => setSelectedImage(img)}
              formatMessageContent={formatMessageContent}
            />
          ))
        )}

        {/* Loading typing bubble */}
        {isLoading && (
          <div style={{ display: 'flex', justifyContent: 'flex-start', width: '100%' }}>
            <div className="glass-card" style={{ padding: '12px 18px' }}>
              <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                <span className="glow-accent-cyan" style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Assisting you...</span>
                <div style={{ display: 'flex', gap: '3px', marginLeft: '6px' }}>
                  <div style={{ width: '4px', height: '4px', borderRadius: '50%', background: 'var(--accent-cyan)', animation: 'bounce 1.4s infinite ease-in-out both' }} />
                  <div style={{ width: '4px', height: '4px', borderRadius: '50%', background: 'var(--accent-cyan)', animation: 'bounce 1.4s infinite ease-in-out both 0.2s' }} />
                  <div style={{ width: '4px', height: '4px', borderRadius: '50%', background: 'var(--accent-cyan)', animation: 'bounce 1.4s infinite ease-in-out both 0.4s' }} />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Citation Details Card (Overlay modal) */}
      {selectedCitation && (
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          background: 'rgba(0,0,0,0.4)',
          backdropFilter: 'blur(4px)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 10
        }}>
          <div className="glass-panel" style={{ width: '90%', maxWidth: '500px', padding: '24px', position: 'relative' }}>
            <button 
              onClick={() => setSelectedCitation(null)}
              style={{
                position: 'absolute',
                top: '16px',
                right: '16px',
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                color: 'var(--text-muted)'
              }}
            >
              <X style={{ width: '20px' }} />
            </button>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
              <FileText style={{ color: 'var(--accent-cyan)', width: '24px', height: '24px' }} />
              <div>
                <h3 style={{ fontSize: '14px', fontWeight: 600 }}>{selectedCitation.filename}</h3>
                <p style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                  Subject: {selectedCitation.subject} | Page: {selectedCitation.page}
                </p>
              </div>
            </div>
            
            <div className="glass-card" style={{ padding: '16px', background: 'rgba(0,0,0,0.2)', maxHeight: '200px', overflowY: 'auto', marginBottom: '16px' }}>
              <p style={{ fontSize: '12px', lineHeight: '1.6', color: 'var(--text-primary)', fontStyle: 'italic' }}>
                "{selectedCitation.text || "Segment text content loaded in search results."}"
              </p>
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                Chunk ID: {selectedCitation.chunk_id}
              </div>
              <div style={{ 
                fontSize: '11px', 
                color: 'var(--accent-purple)', 
                background: 'rgba(168, 85, 247, 0.08)',
                padding: '3px 8px',
                borderRadius: '6px',
                fontWeight: 600
              }}>
                Reranker Score: {selectedCitation.score}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Image Lightbox (Overlay modal) */}
      {selectedImage && (
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          background: 'rgba(0,0,0,0.8)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 20
        }}>
          <button 
            onClick={() => setSelectedImage(null)}
            style={{
              position: 'absolute',
              top: '24px',
              right: '24px',
              background: 'var(--glass-bg)',
              border: '1px solid var(--glass-border)',
              borderRadius: '50%',
              padding: '8px',
              cursor: 'pointer',
              color: '#fff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <X style={{ width: '24px', height: '24px' }} />
          </button>
          <img 
            src={selectedImage.url} 
            alt="Expanded context" 
            style={{ maxWidth: '90%', maxHeight: '70vh', objectFit: 'contain', borderRadius: '8px', boxShadow: '0 8px 32px rgba(0,0,0,0.5)' }}
          />
          {selectedImage.description && (
            <div className="glass-panel" style={{ marginTop: '20px', maxWidth: '80%', padding: '16px 24px', textAlign: 'center' }}>
              <p style={{ fontSize: '13px', color: 'var(--text-primary)', lineHeight: '1.6' }}>
                {selectedImage.description}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Chat Form panel */}
      <div style={{ padding: '20px 24px', borderTop: '1px solid var(--glass-border)' }}>
        <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '12px' }}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
            placeholder={isLoading ? "Please wait..." : "Ask your notes: 'What is Paging?' or 'Explain normalization'..."}
            className="input-glass"
            style={{ flex: 1, padding: '14px 18px', fontSize: '13px' }}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="btn-glass btn-primary"
            style={{ padding: '14px 20px' }}
          >
            <Send style={{ width: '16px', height: '16px' }} />
          </button>
        </form>
      </div>

      {/* Bounce keyframe injection for typing animation */}
      <style>{`
        @keyframes bounce {
          0%, 80%, 100% { transform: scale(0); }
          40% { transform: scale(1.0); }
        }
      `}</style>
    </div>
  );
};
