# 🤖 RAG System with Conversational Memory

A powerful Retrieval-Augmented Generation (RAG) system that allows you to upload multiple documents and have intelligent conversations with AI while maintaining context.

## ✨ Features

- **📚 Multiple Document Support**: Upload multiple PDF, TXT, and MD files simultaneously
- **🧠 Conversational Memory**: AI remembers your conversation context across questions
- **🔄 Simple Controls**: Just "Reset Chat" to make AI forget previous conversation
- **💬 Modern Chat Interface**: Clean, scrollable chat with user/AI message bubbles
- **📄 Document Management**: Remove individual documents or upload new ones
- **🚀 FastAPI Backend**: Robust REST API with comprehensive error handling
- **⚡ Groq LLM**: Fast AI responses powered by Groq's language models
- **🔍 Smart Search**: ChromaDB vector database for intelligent document retrieval

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Create virtual environment
python -m venv ragenv3

# Activate (Windows)
ragenv3\Scripts\activate

# Activate (Linux/Mac)
source ragenv3/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys
Create a `.env` file in the project root:
```env
GROQ_API_KEY=your_groq_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
```

### 3. Start Backend
```bash
python fast_api.py
```
Backend will run on: http://localhost:8000

### 4. Start Frontend
```bash
cd rag-frontend
npm start
```
Frontend will open at: http://localhost:3000

## 🎯 How to Use

1. **Upload Documents**: Select multiple files (PDF, TXT, MD) and click "Upload & Index"
2. **Ask Questions**: Type questions about your documents in the chat
3. **Reset Chat**: Click "Reset Chat" when you want AI to forget the conversation
4. **Manage Documents**: Remove individual documents or upload new ones

## 🏗️ Architecture

- **Frontend**: React with modern chat interface
- **Backend**: FastAPI with RAG orchestration
- **Vector DB**: ChromaDB for document embeddings
- **LLM**: Groq for AI responses
- **Embeddings**: Google AI for document processing
- **Memory**: LangChain ConversationBufferWindowMemory

## 📁 Project Structure

```
project/
├── rag.py                 # Core RAG system with memory
├── fast_api.py           # FastAPI backend server
├── requirements.txt      # Python dependencies
├── rag-frontend/        # React frontend application
│   ├── src/
│   │   ├── App.js       # Main React component
│   │   └── App.css      # Styling
│   └── package.json
└── README.md
```

## 🔧 API Endpoints

- `GET /health` - Check backend status
- `POST /index` - Upload and index multiple documents
- `POST /ask` - Ask questions with conversation memory
- `POST /clear-memory` - Reset AI conversation memory
- `GET /documents` - List indexed documents
- `GET /stats` - System statistics

## 🎨 Frontend Features

- **Multiple File Upload**: Select and upload multiple documents at once
- **Document Management**: View and remove individual documents
- **Chat Interface**: Modern chat UI with message history
- **Auto-scroll**: Chat automatically scrolls to latest messages
- **Keyboard Shortcuts**: Enter to send, Shift+Enter for new lines
- **Status Indicators**: Real-time backend connection status

## 🚀 Getting Started

1. Follow the setup steps above
2. Upload your documents
3. Start asking questions!
4. Use "Reset Chat" when you want a fresh conversation

## 📝 Notes

- The system maintains conversation context until you reset the chat
- Documents are processed in chunks for optimal retrieval
- All uploaded files are temporarily stored and then deleted after processing
- The system supports PDF, TXT, and MD file formats

---

**Happy chatting with your documents! 🎉**
