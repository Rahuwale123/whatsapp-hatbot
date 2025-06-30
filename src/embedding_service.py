"""
This module provides functionalities for text embedding and semantic search using ChromaDB.
It leverages a SentenceTransformer model to generate embeddings and stores/retrieves
text chunks efficiently from a ChromaDB collection.
"""

from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional, Tuple
import chromadb
from chromadb.utils import embedding_functions
from chromadb.api import EmbeddingFunction, Embeddings
import os

# Custom embedding function for ChromaDB using SentenceTransformer
class CustomSentenceTransformerEmbeddingFunction(EmbeddingFunction):
    def __init__(self, model: SentenceTransformer):
        self._model = model

    def __call__(self, texts: List[str]) -> Embeddings:
        # Ensure texts are not empty or just whitespace
        non_empty_texts = [text for text in texts if text.strip()]
        if not non_empty_texts:
            return []
        return self._model.encode(non_empty_texts).tolist()

# Global embedding model instance and ChromaDB client/collection
_embedding_model: Optional[SentenceTransformer] = None
_chroma_client: Optional[chromadb.Client] = None
_chroma_collection: Optional[chromadb.Collection] = None
_collection_name: str = "pdf_chunks_collection" # Name of the ChromaDB collection

def initialize_embedding_service(model_name: str = "all-MiniLM-L6-v2", persist_directory: str = "chroma_db") -> bool:
    """
    Initializes the SentenceTransformer embedding model and ChromaDB client.
    Creates or retrieves the ChromaDB collection for storing PDF embeddings.

    Args:
        model_name: The name of the pre-trained SentenceTransformer model to load.
        persist_directory: The directory path where ChromaDB will store its data.

    Returns:
        True if both the embedding model and ChromaDB are initialized successfully,
        False otherwise.
    """
    global _embedding_model, _chroma_client, _chroma_collection

    print(f"[Embedding] Initializing embedding model: {model_name}")
    try:
        _embedding_model = SentenceTransformer(model_name)
        print("[Embedding] Embedding model loaded successfully.")
    except Exception as e:
        print(f"[❌ ERROR] Failed to load embedding model '{model_name}': {e}")
        _embedding_model = None
        return False
    
    print(f"[ChromaDB] Initializing ChromaDB client in persistent mode: {persist_directory}")
    try:
        # Ensure the persistence directory exists
        os.makedirs(persist_directory, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=persist_directory)

        # Use the custom embedding function for the collection
        custom_ef = CustomSentenceTransformerEmbeddingFunction(model=_embedding_model)

        _chroma_collection = _chroma_client.get_or_create_collection(
            name=_collection_name,
            embedding_function=custom_ef # Use our custom embedding function
        )
        print(f"[ChromaDB] Collection '{_collection_name}' ready. Current count: {_chroma_collection.count()} documents.")
        return True
    except Exception as e:
        print(f"[❌ ERROR] Failed to initialize ChromaDB client or collection: {e}")
        _chroma_client = None
        _chroma_collection = None
        return False

def embed_text(text: str) -> Optional[List[float]]:
    """
    Generates an embedding vector for the given text using the initialized model.

    Args:
        text: The text string to embed.

    Returns:
        A list of floats representing the embedding vector, or None if the
        embedding model is not initialized or text is empty.
    """
    if _embedding_model:
        if not text.strip(): # Check for empty or whitespace-only strings
            print("[Embedding] Cannot embed empty or whitespace-only text.")
            return None
        return _embedding_model.encode(text).tolist()
    print("[❌ ERROR] Embedding model not initialized. Cannot embed text.")
    return None

def process_and_store_pdf_chunks(chunks: List[str]) -> None:
    """
    Stores a list of text chunks into the ChromaDB collection.
    ChromaDB will automatically embed the chunks using the configured embedding function.

    Args:
        chunks: A list of text strings, where each string is a document chunk.
    """
    if not _chroma_collection:
        print("[❌ ERROR] ChromaDB collection not initialized. Cannot store document chunks.")
        return

    if not chunks:
        print("[ChromaDB] No chunks provided to store.")
        return

    # Generate unique IDs for each chunk. Simple index-based IDs for now.
    ids = [f"chunk_{i}" for i in range(len(chunks))]

    print(f"[ChromaDB] Adding {len(chunks)} document chunks to collection '{_collection_name}'...")
    try:
        # ChromaDB handles embedding internally using the collection's embedding_function
        _chroma_collection.add(
            documents=chunks,
            ids=ids
        )
        print(f"[ChromaDB] Successfully added {len(chunks)} chunks. Total documents: {_chroma_collection.count()}")
    except Exception as e:
        print(f"[❌ ERROR] Failed to add documents to ChromaDB collection: {e}")

def search_chunks(query_text: str, top_k: int = 3) -> List[str]:
    """
    Performs a semantic search over stored document chunks in ChromaDB.

    Args:
        query_text: The text query to search for relevant chunks.
        top_k: The number of top similar results to retrieve.

    Returns:
        A list of strings, where each string is a relevant text chunk from the
        ChromaDB collection. Returns an empty list if no results are found or
        an error occurs.
    """
    if not _chroma_collection:
        print("[❌ ERROR] ChromaDB collection not initialized. Cannot perform search.")
        return []

    if not query_text.strip():
        print("[Embedding] Query text is empty or whitespace-only. Cannot search.")
        return []

    print(f"[ChromaDB] Searching collection '{_collection_name}' for query: '{query_text[:50]}...'")
    try:
        # ChromaDB handles embedding the query text internally using the collection's embedding_function
        results = _chroma_collection.query(
            query_texts=[query_text],
            n_results=top_k,
            include=['documents'] # Request to include the original text documents
        )
        
        # Extract and return the relevant text documents
        if results and results['documents'] and results['documents'][0]:
            relevant_chunks = results['documents'][0]
            print(f"[ChromaDB] Found {len(relevant_chunks)} relevant results.")
            return relevant_chunks
        else:
            print("[ChromaDB] No relevant documents found.")
            return []
    except Exception as e:
        print(f"[❌ ERROR] Failed to search ChromaDB: {e}")
        return [] 