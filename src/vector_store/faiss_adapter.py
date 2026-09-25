import logging
from typing import List, Tuple
import numpy as np
from .base import VectorStoreAdapter

logger = logging.getLogger(__name__)

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("faiss-cpu not available. Falling back to NumPy exact-match cosine similarity.")

class FaissAdapter(VectorStoreAdapter):
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.ids: List[str] = []
        
        if FAISS_AVAILABLE:
            # IndexFlatIP uses inner product. If vectors are normalized, IP == Cosine Similarity
            self.index = faiss.IndexFlatIP(dimension)
        else:
            self.index = None
            self.embeddings = None

    def add_embeddings(self, ids: List[str], embeddings: np.ndarray):
        if len(ids) != embeddings.shape[0]:
            raise ValueError("Number of IDs must match number of embeddings.")
            
        # Normalize embeddings for cosine similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        # Avoid division by zero
        norms[norms == 0] = 1 
        normalized_embeddings = embeddings / norms
        
        self.ids.extend(ids)
        
        if FAISS_AVAILABLE:
            self.index.add(normalized_embeddings.astype(np.float32))
        else:
            if self.embeddings is None:
                self.embeddings = normalized_embeddings
            else:
                self.embeddings = np.vstack([self.embeddings, normalized_embeddings])

    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Tuple[str, float]]:
        if not self.ids:
            return []
            
        # Normalize query
        norm = np.linalg.norm(query_embedding)
        if norm > 0:
            query_embedding = query_embedding / norm
            
        query_embedding = query_embedding.astype(np.float32).reshape(1, -1)
        
        # Bound k by the number of stored embeddings
        k = min(k, len(self.ids))
        
        if FAISS_AVAILABLE:
            D, I = self.index.search(query_embedding, k)
            results = []
            for score, idx in zip(D[0], I[0]):
                if idx != -1 and idx < len(self.ids):
                    # Clip score to [0, 1] bounds just in case
                    clipped_score = max(0.0, min(1.0, float(score)))
                    results.append((self.ids[idx], clipped_score))
            return results
        else:
            # NumPy fallback
            if self.embeddings is None:
                return []
                
            similarities = np.dot(self.embeddings, query_embedding.T).flatten()
            
            # Get top k indices
            top_k_idx = similarities.argsort()[-k:][::-1]
            
            results = []
            for idx in top_k_idx:
                clipped_score = max(0.0, min(1.0, float(similarities[idx])))
                results.append((self.ids[idx], clipped_score))
            return results
