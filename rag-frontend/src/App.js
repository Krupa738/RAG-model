import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  const [files, setFiles] = useState([]);
  const [question, setQuestion] = useState('');
  const [conversation, setConversation] = useState([]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('');
  const [backendStatus, setBackendStatus] = useState('unknown');
  const [currentDocuments, setCurrentDocuments] = useState([]);
  const chatEndRef = useRef(null);

  const API_BASE = 'http://localhost:8000';

  // Auto-scroll to bottom of chat
  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [conversation]);

  // Check backend health on component mount
  useEffect(() => {
    checkHealth();
  }, []);

  const checkHealth = async () => {
    try {
      const response = await fetch(`${API_BASE}/health`);
      const data = await response.json();
      setBackendStatus(data.status);
      setStatus(`Backend: ${data.status}`);
    } catch (error) {
      setBackendStatus('error');
      setStatus(`Backend Error: ${error.message}. Make sure the backend is running on port 8000.`);
    }
  };

  const uploadFiles = async () => {
    if (files.length === 0) {
      setStatus('Please select files first');
      return;
    }

    if (backendStatus !== 'healthy') {
      setStatus('Backend is not healthy. Please check the backend first.');
      return;
    }

    setLoading(true);
    setStatus('Uploading and indexing documents...');

    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });
    formData.append('chunk_size', 1200);
    formData.append('chunk_overlap', 150);

    try {
      const response = await fetch(`${API_BASE}/index`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      
      if (response.ok) {
        const documentNames = files.map(file => file.name);
        setCurrentDocuments(documentNames);
        setStatus(`${files.length} document(s) indexed successfully! ${data.chunks_indexed} chunks created.`);
        // Clear conversation when new documents are uploaded
        setConversation([]);
        setFiles([]); // Clear file input
      } else {
        setStatus(`Error: ${data.detail || 'Failed to index documents'}`);
      }
    } catch (error) {
      setStatus(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const removeDocument = (documentName) => {
    setCurrentDocuments(prev => prev.filter(doc => doc !== documentName));
    if (currentDocuments.length === 1) {
      setConversation([]); // Clear conversation if removing last document
    }
    setStatus(`Document "${documentName}" removed.`);
  };

  const askQuestion = async () => {
    if (!question.trim()) {
      setStatus('Please enter a question');
      return;
    }

    if (backendStatus !== 'healthy') {
      setStatus('Backend is not healthy. Please check the backend first.');
      return;
    }

    if (currentDocuments.length === 0) {
      setStatus('Please upload documents first before asking questions.');
      return;
    }

    setLoading(true);
    setStatus('Processing your question...');

    const formData = new FormData();
    formData.append('question', question);

    try {
      const response = await fetch(`${API_BASE}/ask`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      
      if (response.ok) {
        // Add to conversation history
        const newConversation = [
          ...conversation,
          {
            question: question,
            answer: data.answer,
            sources: data.sources || [],
            timestamp: new Date().toLocaleTimeString()
          }
        ];
        setConversation(newConversation);
        setQuestion(''); // Clear input for next question
        setStatus('Question answered successfully!');
      } else {
        setStatus(`Error: ${data.detail || 'Failed to process question'}`);
      }
    } catch (error) {
      setStatus(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const resetChat = async () => {
    if (backendStatus !== 'healthy') {
      setStatus('Backend is not healthy. Please check the backend first.');
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/clear-memory`, {
        method: 'POST',
      });

      if (response.ok) {
        setConversation([]);
        setStatus('Chat reset successfully! AI has forgotten the previous conversation.');
      } else {
        const data = await response.json();
        setStatus(`Error: ${data.detail || 'Failed to reset chat'}`);
      }
    } catch (error) {
      setStatus(`Error: ${error.message}`);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      askQuestion();
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🚀 Knowledge Navigator: Conversational Assistant</h1>
        <p>Upload documents and have conversations with AI</p>
        <div className="backend-status">
          Backend Status: 
          <span className={`status-indicator ${backendStatus}`}>
            {backendStatus === 'healthy' ? '🟢 Healthy' : 
             backendStatus === 'error' ? '🔴 Error' : '🟡 Unknown'}
          </span>
        </div>
      </header>

      <main className="App-main">
        <div className="section">
          <h2>📁 Document Management</h2>
          {currentDocuments.length > 0 ? (
            <div className="current-documents">
              <h3>Current Documents:</h3>
              {currentDocuments.map((doc, index) => (
                <div key={index} className="document-item">
                  <span className="document-name">📄 {doc}</span>
                  <button 
                    onClick={() => removeDocument(doc)} 
                    className="btn btn-warning btn-small"
                  >
                    ❌ Remove
                  </button>
                </div>
              ))}
              <button onClick={resetChat} className="btn btn-info">
                🔄 Reset Chat (AI forgets conversation)
              </button>
            </div>
          ) : (
            <>
              <input
                type="file"
                multiple
                accept=".pdf,.txt,.md"
                onChange={(e) => setFiles(Array.from(e.target.files))}
                className="file-input"
              />
              <p className="upload-hint">You can select multiple files (PDF, TXT, MD)</p>
              <button 
                onClick={uploadFiles} 
                disabled={loading || files.length === 0 || backendStatus !== 'healthy'}
                className="btn btn-primary"
              >
                {loading ? 'Processing...' : `Upload & Index ${files.length} Document(s)`}
              </button>
            </>
          )}
        </div>

        {currentDocuments.length > 0 && (
          <>
            <div className="section chat-section">
              <h2>💬 Chat Interface</h2>
              
              <div className="chat-container">
                {conversation.length === 0 ? (
                  <div className="empty-chat">
                    <p>💡 Start a conversation by asking questions about your documents</p>
                  </div>
                ) : (
                  <div className="chat-messages">
                    {conversation.map((item, index) => (
                      <div key={index} className="chat-message">
                        <div className="message question-message">
                          <div className="message-header">
                            <span className="message-type">👤 You</span>
                            <span className="timestamp">{item.timestamp}</span>
                          </div>
                          <div className="message-content">{item.question}</div>
                        </div>
                        <div className="message answer-message">
                          <div className="message-header">
                            <span className="message-type">🤖 AI</span>
                            <span className="timestamp">{item.timestamp}</span>
                          </div>
                          <div className="message-content">{item.answer}</div>
                          {item.sources && item.sources.length > 0 && (
                            <div className="sources">
                              📚 Sources: {item.sources.join(', ')}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                    <div ref={chatEndRef} />
                  </div>
                )}
              </div>

              <div className="chat-input-container">
                <textarea
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type your question here... (Press Enter to send, Shift+Enter for new line)"
                  rows="3"
                  className="question-input"
                  disabled={loading}
                />
                <button 
                  onClick={askQuestion} 
                  disabled={loading || !question.trim()}
                  className="btn btn-secondary send-btn"
                >
                  {loading ? '⏳ Processing...' : '📤 Send'}
                </button>
              </div>
            </div>
          </>
        )}

        <div className="section">
          <h2>🔧 System Status</h2>
          <button onClick={checkHealth} className="btn btn-info">
            Refresh Backend Status
          </button>
        </div>

        {status && (
          <div className="status-box">
            {status}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
