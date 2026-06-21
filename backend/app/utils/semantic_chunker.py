import re
import math
import logging
from typing import List

logger = logging.getLogger(__name__)

def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences using regex, avoiding common abbreviations.
    """
    # Regex splitting on punctuation followed by whitespace, ignoring common abbreviations
    sentence_end = re.compile(
        r'(?<!\be\.g)'       # not e.g.
        r'(?<!\bi\.e)'       # not i.e.
        r'(?<!\bvs)'         # not vs.
        r'(?<!\bal)'         # not et al.
        r'(?<!\bDr)'         # not Dr.
        r'(?<!\bMr)'         # not Mr.
        r'(?<!\bMrs)'        # not Mrs.
        r'(?<!\bMs)'         # not Ms.
        r'(?<!\bProf)'       # not Prof.
        r'(?<=[.?!])\s+'     # split on .?! followed by space
    )
    raw_sentences = sentence_end.split(text)
    return [s.strip() for s in raw_sentences if s.strip()]

def tokenize(text: str) -> List[str]:
    """
    Tokenize sentence into words, lowercasing and removing punctuation.
    """
    clean_text = re.sub(r'[^\w\s]', '', text.lower())
    return [word for word in clean_text.split() if word]

def compute_tfidf_vectors(sentences: List[str]) -> List[dict]:
    """
    Compute a simple TF-IDF representation for a list of sentences (as sparse dictionaries).
    """
    tokenized_sentences = [tokenize(s) for s in sentences]
    num_sentences = len(sentences)
    
    if num_sentences == 0:
        return []
        
    # Document frequency
    df = {}
    for tokens in tokenized_sentences:
        unique_tokens = set(tokens)
        for t in unique_tokens:
            df[t] = df.get(t, 0) + 1
            
    # Compute IDF
    idf = {}
    for term, count in df.items():
        # log(1 + total / (1 + count)) for smoothing
        idf[term] = math.log(1 + num_sentences / (1 + count))
        
    # Compute TF-IDF vectors
    tfidf_vectors = []
    for tokens in tokenized_sentences:
        vector = {}
        total_tokens = len(tokens)
        if total_tokens == 0:
            tfidf_vectors.append({})
            continue
            
        # Term Frequency
        tf = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1
            
        # TF-IDF
        for term, count in tf.items():
            vector[term] = (count / total_tokens) * idf.get(term, 0.0)
            
        tfidf_vectors.append(vector)
        
    return tfidf_vectors

def cosine_similarity(vec1: dict, vec2: dict) -> float:
    """
    Calculate cosine similarity between two sparse TF-IDF vectors.
    """
    if not vec1 or not vec2:
        return 0.0
        
    # Intersection of keys
    intersection = set(vec1.keys()) & set(vec2.keys())
    
    dot_product = sum(vec1[x] * vec2[x] for x in intersection)
    
    sum1 = sum(val ** 2 for val in vec1.values())
    sum2 = sum(val ** 2 for val in vec2.values())
    
    if sum1 == 0 or sum2 == 0:
        return 0.0
        
    return dot_product / (math.sqrt(sum1) * math.sqrt(sum2))

class SemanticChunker:
    def __init__(self, similarity_threshold: float = 0.15, min_chunk_chars: int = 150, max_chunk_chars: int = 600):
        self.similarity_threshold = similarity_threshold
        self.min_chunk_chars = min_chunk_chars
        self.max_chunk_chars = max_chunk_chars
        
    def chunk_text(self, text: str) -> List[str]:
        """
        Chunks input text semantically using TF-IDF sentence boundary similarities.
        """
        sentences = split_into_sentences(text)
        if not sentences:
            return []
            
        if len(sentences) == 1:
            return [sentences[0]]
            
        # Compute sentence vectors
        vectors = compute_tfidf_vectors(sentences)
        
        chunks = []
        current_chunk_sentences = [sentences[0]]
        current_chunk_len = len(sentences[0])
        
        for i in range(1, len(sentences)):
            curr_sentence = sentences[i]
            curr_vector = vectors[i]
            prev_vector = vectors[i-1]
            
            # Calculate similarity to previous sentence
            sim = cosine_similarity(curr_vector, prev_vector)
            
            # Conditions to split:
            # 1. Similarity drops below threshold.
            # 2. Current chunk has reached the minimum character size.
            # 3. OR the current chunk would exceed the maximum size if we added this sentence.
            would_exceed_max = (current_chunk_len + len(curr_sentence) + 1) > self.max_chunk_chars
            reached_min = current_chunk_len >= self.min_chunk_chars
            
            # If similarity is low and we have enough chars, or if it will overflow the max limit
            if (sim < self.similarity_threshold and reached_min) or (reached_min and would_exceed_max):
                # Save previous chunk
                chunks.append(" ".join(current_chunk_sentences))
                # Reset
                current_chunk_sentences = [curr_sentence]
                current_chunk_len = len(curr_sentence)
            else:
                current_chunk_sentences.append(curr_sentence)
                current_chunk_len += len(curr_sentence) + 1  # +1 for space
                
        # Add the final remaining chunk
        if current_chunk_sentences:
            chunks.append(" ".join(current_chunk_sentences))
            
        return chunks
