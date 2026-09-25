import json
import logging
from typing import List
from sentence_transformers import SentenceTransformer, util
import os

logger = logging.getLogger(__name__)

class SkillMatcher:
    def __init__(self, ontology_path: str = None):
        if ontology_path is None:
            # Default to the adjacent json file
            ontology_path = os.path.join(os.path.dirname(__file__), '..', 'ontology', 'skills.json')
            
        with open(ontology_path, 'r') as f:
            self.ontology = json.load(f)
            
        # Create a flattened list of all variants and a mapping back to the canonical skill name
        self.variant_to_canonical = {}
        for canonical, variants in self.ontology.items():
            for variant in variants:
                self.variant_to_canonical[variant.lower()] = canonical
                
        self.skill_variants = list(self.variant_to_canonical.keys())
        
        try:
            # Try to load the model from the local offline directory
            if os.path.exists('./models/all-MiniLM-L6-v2'):
                self.model = SentenceTransformer('./models/all-MiniLM-L6-v2')
            else:
                # Fallback to downloading from HuggingFace (e.g., in CI environments)
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.skill_embeddings = self.model.encode(self.skill_variants, convert_to_tensor=True)
        except Exception as e:
            logger.error(f"Failed to load sentence-transformers model. {e}")
            self.model = None

    def extract_skills(self, text: str, threshold: float = 0.8) -> List[str]:
        if not self.model or not text.strip():
            return []
            
        # We split text into words or short phrases. 
        import re
        # Split by spaces and punctuation (excluding typical skill characters like '.' in 'React.js' or '#' in 'C#')
        # A simple approach: replace commas, newlines, bullet points, and parens with spaces, then split by whitespace.
        cleaned_text = re.sub(r'[,•\n\(\)\/\|\;]', ' ', text)
        tokens = [t.strip().rstrip('.') for t in cleaned_text.split() if t.strip()]
        
        if not tokens:
            return []
            
        token_embeddings = self.model.encode(tokens, convert_to_tensor=True)
        
        # Compute cosine similarities between tokens and skill variants
        cosine_scores = util.cos_sim(token_embeddings, self.skill_embeddings)
        
        matched_skills = set()
        for i in range(len(tokens)):
            # Find the best matching skill variant for this token
            best_match_idx = cosine_scores[i].argmax().item()
            best_score = cosine_scores[i][best_match_idx].item()
            
            if best_score >= threshold:
                matched_variant = self.skill_variants[best_match_idx]
                canonical_skill = self.variant_to_canonical[matched_variant]
                matched_skills.add(canonical_skill)
                
        return list(matched_skills)
