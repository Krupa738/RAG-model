from rag import RAGWithMemory

# Initialize RAG system
test = RAGWithMemory(system_prompt_file="system_prompt.txt", memory_window=5)

# First, index the PDF document
print("Indexing document...")
num_chunks = test.index_document("chroma_db/e-katha.pdf")
print(f"Indexed {num_chunks} chunks from the document")

# Now ask a question
print("\nAsking question...")
result = test.ask("How much is the payable tax?")
print("Answer:", result['answer'])
print("Sources:", result['sources'])