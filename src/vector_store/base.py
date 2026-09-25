from abc import ABC, abstractmethod
from typing import List, Tuple
import numpy as np

class VectorStoreAdapter(ABC):
    @abstractmethod
    def add_embeddings(self, ids: List[str], embeddings: np.ndarray):
        """Adds a batch of embeddings to the vector store with associated IDs."""
        pass

    @abstractmethod
    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Tuple[str, float]]:
        """Searches for the top-k nearest neighbors.
        Returns a list of tuples (id, similarity_score).
        Similarity score should be normalized between 0 and 1 if possible.
        """
        pass
