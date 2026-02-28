from typing import List, Dict, Any
from pydantic import BaseModel, Field
import random
import uuid
import os
import chromadb

# Use local PersistentClient — no Docker server needed.
# Data is saved to ./chroma_data_v2 inside the backend directory.
_CHROMA_DATA_PATH = os.path.join(os.path.dirname(__file__), "chroma_data_v2")
chroma_client = chromadb.PersistentClient(path=_CHROMA_DATA_PATH)


class MemoryItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: int
    content: str
    importance: float # 0.0 to 1.0
    entropy_level: float = 0.0 # How "degraded" or hallucinated this memory is

class MemorySystem:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.short_term: List[MemoryItem] = []
        
        # Connect to a shared ChromaDB collection for all agents' long-term memory
        self.collection = chroma_client.get_or_create_collection(name="civilization_memories")
        
    def add_memory(self, content: str, importance: float, timestamp: int):
        item = MemoryItem(content=content, importance=importance, timestamp=timestamp)
        self.short_term.append(item)
        
    def reflect_and_summarize(self, current_time: int) -> List[MemoryItem]:
        """
        Periodically compresses short-term memories into long-term.
        This is where ENTROPY (hallucination) is artificially introduced to create myths.
        """
        summarized = []
        for mem in self.short_term:
            if mem.importance >= 0.5:
                # Add noise (entropy) based on time passed or random chance
                degraded_content = self._apply_entropy(mem.content)
                mem.content = degraded_content
                mem.entropy_level += 0.1
                
                import random
                # Provide explicit embeddings to bypass ChromaDB's default embedding function which crashes on some macOS systems with ONNX/CoreML errors
                mock_embedding = [random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)]
                
                # Store to ChromaDB
                self.collection.upsert(
                    ids=[mem.id],
                    documents=[mem.content],
                    metadatas=[{
                        "agent_id": self.agent_id,
                        "timestamp": mem.timestamp,
                        "importance": mem.importance,
                        "entropy_level": mem.entropy_level
                    }],
                    embeddings=[mock_embedding]
                )
                summarized.append(mem)
        
        # Clear short term after reflecting
        self.short_term = []
        return summarized

    def _apply_entropy(self, content: str) -> str:
        # Placeholder for LLM-based hallucination injection
        # e.g., "I saw a large wolf" -> "I saw a giant beast with red eyes"
        # If random.random() < 0.2: LLM rewrite with exaggeration prompt
        return content

    def retrieve_relevant(self, query: str, top_k: int = 5) -> List[Any]:
        # Search ChromaDB
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        return results
