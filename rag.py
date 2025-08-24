import os
import asyncio
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

# LangChain core
from langchain.schema import Document
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Vector store
from langchain_chroma import Chroma

# Embeddings + LLMs
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_groq import ChatGroq

# Loaders
from langchain_community.document_loaders import PyPDFLoader, TextLoader

# Retrieval chain + memory
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.memory import ConversationBufferWindowMemory


# ---------------------------
# Setup & Config
# ---------------------------
load_dotenv()

try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

PERSIST_DIR = str(Path("./chroma_db").resolve())
COLLECTION_NAME = "rag_doc"
DEFAULT_CHROMA_SPACE = "cosine"

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")


# ---------------------------
# Core helpers
# ---------------------------
def load_docs(file_path: str) -> List[Document]:
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return PyPDFLoader(file_path).load()
    if ext in [".txt", ".md", ".text"]:
        return TextLoader(file_path, encoding="utf-8").load()
    raise ValueError(f"Unsupported file type: {ext}")


def chunk_docs(docs: List[Document], size=1200, overlap=150) -> List[Document]:
    return RecursiveCharacterTextSplitter(
        chunk_size=size, chunk_overlap=overlap
    ).split_documents(docs)


def get_embeddings():
    return GoogleGenerativeAIEmbeddings(model="models/embedding-001")


def get_vectorstore(emb, space=DEFAULT_CHROMA_SPACE) -> Chroma:
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=emb,
        persist_directory=PERSIST_DIR,
        collection_metadata={"hnsw:space": space},
    )


def get_llm():
    return ChatGroq(
        api_key=GROQ_API_KEY,
        model=GROQ_MODEL,
        temperature=0.2,
    )


# ---------------------------
# Memory-enabled RAG
# ---------------------------
class RAGWithMemory:
    def __init__(self, system_prompt_file: str, k: int = 4, memory_window: int = 5):
        self.system_prompt = Path(system_prompt_file).read_text(encoding="utf-8").strip()
        self.emb = get_embeddings()
        self.vs = get_vectorstore(self.emb)
        self.llm = get_llm()
        self.k = k

        # Conversation memory (keeps last N exchanges)
        self.memory = ConversationBufferWindowMemory(
            k=memory_window, return_messages=True, memory_key="history"
        )        # Build prompt template with memory placeholder and context
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "Context: {context}\n\nQuestion: {input}"),
        ])

    def index_document(self, file_path: str, chunk_size=1200, chunk_overlap=150):
        docs = load_docs(file_path)
        chunks = chunk_docs(docs, size=chunk_size, overlap=chunk_overlap)
        self.vs.add_documents(chunks)
        return len(chunks)

    def ask(self, query: str) -> Dict[str, Any]:
        retriever = self.vs.as_retriever(search_kwargs={"k": self.k})
        combine_docs = create_stuff_documents_chain(llm=self.llm, prompt=self.prompt)
        rag_chain = create_retrieval_chain(retriever, combine_docs)

        # Invoke with memory
        inputs = {"input": query, "history": self.memory.load_memory_variables({})["history"]}
        result = rag_chain.invoke(inputs)

        # Save turn in memory
        self.memory.save_context({"input": query}, {"output": result.get("answer", "")})

        return {
            "answer": result.get("answer", ""),
            "sources": [d.metadata.get("source", "uploaded") for d in result.get("context", [])],
            "history": self.memory.load_memory_variables({})["history"],
        }
