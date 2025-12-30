import streamlit as st
import os
import chromadb
from chromadb.config import Settings
import google.generativeai as genai
from typing import List, Dict, Any, Optional
import datetime
import uuid

from clara_app.constants import API_KEY

# Configuration
DB_PATH = os.environ.get("CLARA_MEMORY_DB_PATH", "./clara_memory_db")
COLLECTION_NAME = "clara_thoughts"

@st.cache_resource
def _get_client():
    return chromadb.PersistentClient(path=DB_PATH)

def _get_collection():
    client = _get_client()
    return client.get_or_create_collection(name=COLLECTION_NAME)

def get_embedding(text: str) -> Optional[List[float]]:
    """
    Generate an embedding using Google Gemini models/embedding-001.
    """
    if not API_KEY:
        return None
    
    try:
        # Use the 'embedding-001' model optimized for texts
        result = genai.embed_content(
            model="models/embedding-001",
            content=text,
            task_type="retrieval_document",
            title="Clara Memory"
        )
        return result['embedding']
    except Exception as e:
        print(f"Embedding error: {e}")
        return None

def store_memory(username: str, text: str, metadata: Dict[str, Any]):
    """
    Store a text memory with associated metadata.
    """
    if not text or not username:
        return

    embedding = get_embedding(text)
    if not embedding:
        return

    collection = _get_collection()
    
    # Ensure standard metadata fields
    # Chroma only supports str, int, float, bool in metadata
    safe_metadata = {}
    for k, v in metadata.items():
        if isinstance(v, (str, int, float, bool)):
            safe_metadata[k] = v
        else:
            safe_metadata[k] = str(v)
            
    safe_metadata["username"] = username
    safe_metadata["timestamp"] = datetime.datetime.now().isoformat()
    
    memory_id = str(uuid.uuid4())
    
    collection.add(
        documents=[text],
        embeddings=[embedding],
        metadatas=[safe_metadata],
        ids=[memory_id]
    )

def search_memories(username: str, query_text: str, n_results: int = 5, min_relevance: float = 0.0) -> List[Dict[str, Any]]:
    """
    Search for similar memories for a specific user.
    """
    if not query_text or not username:
        return []

    # specific embedding for query
    try:
         query_embedding = genai.embed_content(
            model="models/embedding-001",
            content=query_text,
            task_type="retrieval_query"
        )['embedding']
    except Exception:
        return []

    collection = _get_collection()
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where={"username": username} # Filter by user
    )
    
    # Format results
    memories = []
    if results["ids"]:
        for i in range(len(results["ids"][0])):
            memories.append({
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if "distances" in results else 0
            })
            
    return memories

def search_patterns(username: str, tone: str, n_results: int = 5) -> List[Dict[str, Any]]:
    """
    Specific search to find memories with a matching emotional tone.
    Used for the 'Integrity Mirror' functionality.
    """
    collection = _get_collection()
    
    # We want to find memories with the same tone, regardless of semantic content?
    # Actually, we probably want "Recent memories with this tone" or just "any memories with this tone".
    # Querying without embeddings (just metadata filter) is possible in Chroma.
    
    results = collection.get(
        where={"$and": [
            {"username": {"$eq": username}},
            {"tone": {"$eq": tone}}
        ]},
        limit=n_results
    )
    
    memories = []
    if results["ids"]:
        for i in range(len(results["ids"])):
            memories.append({
                "id": results["ids"][i],
                "content": results["documents"][i],
                "metadata": results["metadatas"][i]
            })
            
    return memories
