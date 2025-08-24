from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pathlib import Path
import shutil
import os
from typing import List, Dict, Any, Optional
import logging

from rag import RAGWithMemory, PERSIST_DIR, load_docs, chunk_docs

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create one RAG instance for the whole app
try:
    rag = RAGWithMemory(system_prompt_file="system_prompt.txt", memory_window=5)
    logger.info("RAG system initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize RAG system: {e}")
    rag = None

app = FastAPI(
    title="RAG API with Memory", 
    version="1.0",
    description="A Retrieval-Augmented Generation API with conversation memory and document indexing capabilities",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Check if the API is running and RAG system is available."""
    status = "healthy" if rag else "unhealthy"
    return {
        "status": status,
        "rag_system": "available" if rag else "unavailable",
        "chroma_db": "available" if Path(PERSIST_DIR).exists() else "not_found"
    }

@app.post("/index")
async def index_files(
    files: list[UploadFile] = File(...),
    chunk_size: int = Form(1200),
    chunk_overlap: int = Form(150),
):
    """
    Upload and index multiple documents into ChromaDB.
    
    - **files**: List of documents to upload (PDF, TXT, MD supported)
    - **chunk_size**: Size of text chunks (default: 1200)
    - **chunk_overlap**: Overlap between chunks (default: 150)
    """
    if not rag:
        raise HTTPException(status_code=503, detail="RAG system not available")
    
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    # Validate file types
    allowed_extensions = {'.pdf', '.txt', '.md', '.text'}
    total_chunks = 0
    processed_files = []
    
    # Create uploads directory
    uploads_dir = Path("./_uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        for file in files:
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in allowed_extensions:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Unsupported file type '{file_ext}' for {file.filename}. Allowed: {', '.join(allowed_extensions)}"
                )
            
            # Save uploaded file
            tmp_path = uploads_dir / file.filename
            content = await file.read()
            with open(tmp_path, "wb") as f:
                f.write(content)
            
            # Index the document
            chunks_added = rag.index_document(str(tmp_path), chunk_size, chunk_overlap)
            total_chunks += chunks_added
            processed_files.append(file.filename)
            
            # Clean up temporary file
            tmp_path.unlink()
            
            logger.info(f"Successfully indexed {chunks_added} chunks from {file.filename}")
        
        return {
            "status": "success", 
            "files_processed": processed_files,
            "chunks_indexed": total_chunks,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Clean up any remaining temporary files
        for filename in processed_files:
            tmp_path = uploads_dir / filename
            if tmp_path.exists():
                tmp_path.unlink()
        
        logger.error(f"Error indexing files: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to index documents: {str(e)}")

@app.post("/ask")
async def ask_question(question: str = Form(...)):
    """
    Ask a question with conversation memory.
    
    - **question**: The question to ask
    """
    if not rag:
        raise HTTPException(status_code=503, detail="RAG system not available")
    
    if not question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    try:
        result = rag.ask(question.strip())
        logger.info(f"Question processed: {question[:50]}...")
        return result
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process question: {str(e)}")

@app.get("/documents")
async def list_documents():
    """List all indexed documents in the ChromaDB."""
    if not rag:
        raise HTTPException(status_code=503, detail="RAG system not available")
    
    try:
        # Get collection info
        collection = rag.vs._collection
        if collection:
            count = collection.count()
            return {
                "status": "success",
                "total_documents": count,
                "collection_name": rag.vs.collection_name,
                "persist_directory": PERSIST_DIR
            }
        else:
            return {"status": "no_collection", "message": "No collection found"}
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")

@app.post("/clear")
async def clear_db():
    """Clear the entire ChromaDB store."""
    if not rag:
        raise HTTPException(status_code=503, detail="RAG system not available")
    
    try:
        if Path(PERSIST_DIR).exists():
            shutil.rmtree(PERSIST_DIR)
            logger.info("ChromaDB cleared successfully")
            return {"status": "success", "message": "ChromaDB cleared successfully"}
        else:
            return {"status": "no_db", "message": "No ChromaDB found to clear"}
    except Exception as e:
        logger.error(f"Error clearing ChromaDB: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear ChromaDB: {str(e)}")

@app.post("/clear-memory")
async def clear_memory():
    """Clear the conversation memory."""
    if not rag:
        raise HTTPException(status_code=503, detail="RAG system not available")
    
    try:
        rag.memory.clear()
        logger.info("Conversation memory cleared successfully")
        return {"status": "success", "message": "Conversation memory cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing memory: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear memory: {str(e)}")

@app.get("/memory")
async def get_memory():
    """Get the current conversation memory."""
    if not rag:
        raise HTTPException(status_code=503, detail="RAG system not available")
    
    try:
        memory_vars = rag.memory.load_memory_variables({})
        return {
            "status": "success",
            "memory": memory_vars.get("history", []),
            "memory_window": rag.memory.k
        }
    except Exception as e:
        logger.error(f"Error getting memory: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get memory: {str(e)}")

@app.post("/reindex")
async def reindex_document(
    file_path: str = Form(...),
    chunk_size: int = Form(1200),
    chunk_overlap: int = Form(150)
):
    """
    Reindex an existing document from a file path.
    
    - **file_path**: Path to the document to reindex
    - **chunk_size**: Size of text chunks (default: 1200)
    - **chunk_overlap**: Overlap between chunks (default: 150)
    """
    if not rag:
        raise HTTPException(status_code=503, detail="RAG system not available")
    
    if not Path(file_path).exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    
    try:
        chunks_added = rag.index_document(file_path, chunk_size, chunk_overlap)
        logger.info(f"Successfully reindexed {chunks_added} chunks from {file_path}")
        
        return {
            "status": "success",
            "file_path": file_path,
            "chunks_indexed": chunks_added,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap
        }
    except Exception as e:
        logger.error(f"Error reindexing file {file_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reindex document: {str(e)}")

@app.get("/stats")
async def get_stats():
    """Get system statistics and configuration."""
    if not rag:
        raise HTTPException(status_code=503, detail="RAG system not available")
    
    try:
        collection = rag.vs._collection
        doc_count = collection.count() if collection else 0
        
        return {
            "status": "success",
            "rag_system": {
                "model": rag.llm.model_name if hasattr(rag.llm, 'model_name') else "unknown",
                "temperature": rag.llm.temperature if hasattr(rag.llm, 'temperature') else "unknown",
                "retrieval_k": rag.k,
                "memory_window": rag.memory.k
            },
            "vector_store": {
                "collection_name": rag.vs.collection_name,
                "total_documents": doc_count,
                "persist_directory": PERSIST_DIR
            },
            "system_prompt_length": len(rag.system_prompt)
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
