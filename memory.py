import chromadb
from chromadb.utils import embedding_functions
from logger import logger
from config import settings
from utils import handle_errors, time_it
import datetime
from typing import List, Dict, Any, Optional

class Memory:
    """Long-term memory management using ChromaDB."""

    def __init__(self):
        self.db_path = settings.system.chroma_db_path
        self.client = chromadb.PersistentClient(path=self.db_path)
        
        # Use default embedding function (Sentences Transformer)
        # Note: This runs locally.
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        
        # Initialize collections
        self.episodic = self.client.get_or_create_collection(
            name="episodic_memory",
            embedding_function=self.embedding_fn
        )
        self.preferences = self.client.get_or_create_collection(
            name="user_preferences",
            embedding_function=self.embedding_fn
        )
        
        logger.info(f"Memory system initialized at {self.db_path}")

    @handle_errors("Memory")
    def add_episodic(self, text: str, metadata: Optional[Dict[str, Any]] = None):
        """Adds a new event or interaction to episodic memory."""
        timestamp = datetime.datetime.now().isoformat()
        doc_id = f"epi_{timestamp}"
        
        meta = metadata or {}
        meta["timestamp"] = timestamp
        
        self.episodic.add(
            documents=[text],
            metadatas=[meta],
            ids=[doc_id]
        )
        logger.debug(f"Episodic memory added: {text[:50]}...")

    @handle_errors("Memory")
    def add_preference(self, key: str, value: str):
        """Adds or updates a user preference."""
        doc_id = f"pref_{key}"
        text = f"{key}: {value}"
        
        self.preferences.upsert(
            documents=[text],
            metadatas=[{"key": key, "value": value}],
            ids=[doc_id]
        )
        logger.info(f"Preference updated: {key} = {value}")

    @handle_errors("Memory")
    @time_it
    def search(self, query: str, limit: int = 3) -> List[str]:
        """Searches both episodic and preference memory for relevant information."""
        results = []
        
        # Search preferences first (usually more critical)
        pref_results = self.preferences.query(
            query_texts=[query],
            n_results=limit
        )
        if pref_results["documents"]:
            results.extend(pref_results["documents"][0])
            
        # Search episodic memory
        epi_results = self.episodic.query(
            query_texts=[query],
            n_results=limit
        )
        if epi_results["documents"]:
            results.extend(epi_results["documents"][0])
            
        return list(set(results)) # Deduplicate

    @handle_errors("Memory")
    def clear_all(self):
        """Clears all stored memories. Use with caution."""
        self.client.delete_collection("episodic_memory")
        self.client.delete_collection("user_preferences")
        self.__init__() # Re-init collections
        logger.warning("All memories have been cleared.")
