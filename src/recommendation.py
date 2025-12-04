import faiss
import numpy as np
from openai import OpenAI
from src.config import OPENAI_API_KEY

client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url="https://api.openai.com/v1"
)
    
def generate_embedding(text_list):
    """
    Generates embeddings for a list of songs.
    
    Args:
        text_list: List of dictionaries containing song information
        
    Returns:
        Updated list with embeddings
    """
    for song in text_list:
        try:
            if song.get("vibe_text"):
                completion = client.embeddings.create(
                    model="text-embedding-3-small",
                    input=song["vibe_text"]
                )
                song["embedding"] = completion.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding for {song['title']} by {song['artist']}: {e}")
            song["embedding"] = None
    return text_list

def build_faiss_index(vectors):
    """
    Builds a FAISS index from a list of embedding vectors.
    
    Args:
        vectors: List or numpy array of embedding vectors
        
    Returns:
        Built FAISS index ready for search
    """
    # Convert to numpy array if necessary
    if not isinstance(vectors, np.ndarray):
        vectors = np.array(vectors).astype("float32")
    else:
        vectors = vectors.astype("float32")
    
    # L2 normalization to use cosine similarity
    faiss.normalize_L2(vectors)
    
    # Create index with Inner Product (equivalent to cosine after normalization)
    index = faiss.IndexFlatIP(vectors.shape[1])
    
    # Add vectors to the index
    index.add(vectors)
    
    return index

def search_similar_songs(index, query_vector, k=5):
    """
    Searches for the k most similar songs from a query vector.
    
    Args:
        index: Built FAISS index
        query_vector: Embedding vector of the query song (numpy array)
        k: Number of results to return (default 5)
        
    Returns:
        Tuple (distances, indices) where:
            - distances: Array of similarity scores
            - indices: Array of similar song indices
    """
    # Ensure the vector is in the correct format
    if len(query_vector.shape) == 1:
        query_vector = np.array([query_vector]).astype("float32")
    else:
        query_vector = query_vector.astype("float32")
    
    # L2 normalization of the query vector
    faiss.normalize_L2(query_vector)
    
    # Search for k+1 nearest neighbors (includes the song itself)
    distances, indices = index.search(query_vector, k + 1)
    
    return distances, indices
