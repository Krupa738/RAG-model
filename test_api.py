import requests
import json
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health check endpoint."""
    print("Testing /health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Make sure the server is running.")
    except Exception as e:
        print(f"❌ Error: {e}")
    print("-" * 50)

def test_stats():
    """Test the stats endpoint."""
    print("Testing /stats endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/stats")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"❌ Error: {e}")
    print("-" * 50)

def test_documents():
    """Test the documents endpoint."""
    print("Testing /documents endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/documents")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"❌ Error: {e}")
    print("-" * 50)

def test_index_document():
    """Test the document indexing endpoint."""
    print("Testing /index endpoint...")
    
    # Check if the PDF exists
    pdf_path = Path("chroma_db/e-katha.pdf")
    if not pdf_path.exists():
        print("❌ PDF file not found. Please ensure chroma_db/e-katha.pdf exists.")
        return
    
    try:
        with open(pdf_path, "rb") as f:
            files = {"file": ("e-katha.pdf", f, "application/pdf")}
            data = {"chunk_size": 1200, "chunk_overlap": 150}
            
            response = requests.post(f"{BASE_URL}/index", files=files, data=data)
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"❌ Error: {e}")
    print("-" * 50)

def test_ask_question():
    """Test the ask endpoint."""
    print("Testing /ask endpoint...")
    try:
        data = {"question": "What is this document about?"}
        response = requests.post(f"{BASE_URL}/ask", data=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"❌ Error: {e}")
    print("-" * 50)

def test_memory():
    """Test the memory endpoint."""
    print("Testing /memory endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/memory")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"❌ Error: {e}")
    print("-" * 50)

def test_reindex():
    """Test the reindex endpoint."""
    print("Testing /reindex endpoint...")
    
    pdf_path = "chroma_db/e-katha.pdf"
    if not Path(pdf_path).exists():
        print("❌ PDF file not found. Please ensure chroma_db/e-katha.pdf exists.")
        return
    
    try:
        data = {
            "file_path": pdf_path,
            "chunk_size": 1000,
            "chunk_overlap": 100
        }
        response = requests.post(f"{BASE_URL}/reindex", data=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"❌ Error: {e}")
    print("-" * 50)

def main():
    """Run all API tests."""
    print("🚀 Testing RAG API Endpoints")
    print("=" * 50)
    
    # Test basic endpoints
    test_health()
    test_stats()
    test_documents()
    
    # Test document operations
    test_index_document()
    test_reindex()
    
    # Test RAG functionality
    test_ask_question()
    test_memory()
    
    print("✅ API testing completed!")

if __name__ == "__main__":
    main()
