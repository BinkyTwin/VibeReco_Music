"""
Music Recommendation Pipeline Module

This module orchestrates the complete music recommendation workflow by integrating:
- YouTube Music API for song discovery
- Genius API for lyrics extraction
- OpenRouter AI for emotional/semantic analysis
- OpenAI embeddings for vector representation
- FAISS for similarity search

The MusicPipeline class provides a unified interface for the entire process.
"""

import numpy as np
from src.extraction import get_youtube_recommendations, fetch_lyrics
from src.analysis import analyze_emotional_profile, generate_vibe_text
from src.recommendation import generate_embedding, build_faiss_index, search_similar_songs


class MusicPipeline:
    """
    Orchestrates the complete music recommendation pipeline.
    
    This class manages the end-to-end workflow from song search to recommendations,
    including data extraction, AI analysis, embedding generation, and similarity search.
    
    Attributes:
        status_callback: Optional callback function for logging pipeline progress
    """
    
    def __init__(self, status_callback=None):
        """
        Initialize the MusicPipeline.
        
        Args:
            status_callback: Optional function to call with status updates (e.g., for UI logging)
        """
        self.status_callback = status_callback
        
    def log(self, message):
        """
        Log a message using the status callback if available.
        
        Args:
            message: String message to log
        """
        if self.status_callback:
            self.status_callback(message)
        else:
            print(message)
    
    def run(self, query, limit=10, return_youtube_tracks=False):
        """
        Execute the complete music recommendation pipeline.
        
        This method performs the following steps:
        1. Search for songs on YouTube Music based on the query
        2. Fetch lyrics for each song from Genius
        3. Analyze lyrics using AI to extract emotional/semantic profiles
        4. Generate vibe text descriptions from the analysis
        5. Create embeddings from vibe texts
        6. Build a FAISS index for similarity search
        7. Find and return similar songs
        
        Args:
            query: Search query string (song title, artist, or combination)
            limit: Maximum number of candidate songs to retrieve (default: 10)
            return_youtube_tracks: If True, returns YouTube tracks as intermediate result
            
        Returns:
            If return_youtube_tracks is False:
                tuple: (tracks, distances, indices) where:
                    - tracks: List of song dictionaries with all metadata
                    - distances: Numpy array of similarity scores
                    - indices: Numpy array of song indices in the tracks list
            If return_youtube_tracks is True:
                dict: Contains 'youtube_tracks', 'final_tracks', 'distances', 'indices'
            None values if the pipeline fails at any step
        """
        
        # Step 1: Get YouTube Music recommendations
        self.log("Searching for songs on YouTube Music... - Recherche de chansons sur YouTube Music...")
        tracks = get_youtube_recommendations(query, limit=limit)
        
        if not tracks:
            self.log("No songs found on YouTube Music. - Aucune chanson trouvée sur YouTube Music.")
            if return_youtube_tracks:
                return {"youtube_tracks": None, "final_tracks": None, "distances": None, "indices": None}
            return None, None, None
        
        # Store YouTube tracks for intermediate display
        youtube_tracks = tracks.copy()
        
        self.log(f"{len(tracks)} songs found on YouTube Music - {len(tracks)} chansons trouvées sur YouTube Music")
        
        # Step 2: Fetch lyrics from Genius
        self.log("Fetching lyrics via Genius API... - Récupération des paroles via Genius API...")
        tracks = fetch_lyrics(tracks)
        
        if not tracks:
            self.log("Failed to fetch lyrics. - Échec de la récupération des paroles.")
            return None, None, None
        
        # Store tracks with lyrics status for display
        tracks_with_lyrics = tracks.copy()
        
        lyrics_found = sum(1 for t in tracks if t.get("status") == "found")
        self.log(f"Lyrics found for {lyrics_found}/{len(tracks)} songs - Paroles trouvées pour {lyrics_found}/{len(tracks)} chansons")
        
        # Step 3: Analyze emotional profiles using LLM
        self.log("Emotional and semantic analysis via LLM... - Analyse émotionnelle et sémantique via LLM...")
        for track in tracks:
            if track.get("lyrics") and track.get("status") == "found":
                try:
                    analysis = analyze_emotional_profile(
                        title=track["title"],
                        artist=track["artist"],
                        lyrics=track["lyrics"]
                    )
                    track["analysis"] = analysis
                    self.log(f"  Analysis completed for '{track['title']}' - Analyse complétée pour '{track['title']}'")
                except Exception as e:
                    self.log(f"  Analysis error for '{track['title']}': {str(e)} - Erreur d'analyse pour '{track['title']}': {str(e)}")
                    track["analysis"] = None
            else:
                track["analysis"] = None
                self.log(f"  No lyrics for '{track['title']}' - analysis skipped - Pas de paroles pour '{track['title']}' - analyse ignorée")
        
        analyzed_count = sum(1 for t in tracks if t.get("analysis"))
        self.log(f"{analyzed_count}/{len(tracks)} songs analyzed - {analyzed_count}/{len(tracks)} chansons analysées")
        
        # Step 4: Generate vibe text descriptions
        self.log("Generating vibe descriptions... - Génération des descriptions de vibe...")
        try:
            generate_vibe_text(tracks)
            vibe_count = sum(1 for t in tracks if t.get("vibe_text"))
            self.log(f"{vibe_count} vibe descriptions generated - {vibe_count} descriptions de vibe générées")
        except Exception as e:
            self.log(f"Error generating vibes: {str(e)} - Erreur lors de la génération des vibes: {str(e)}")
        
        # Step 5: Generate embeddings
        self.log("Generating embeddings via OpenAI... - Génération des embeddings via OpenAI...")
        try:
            tracks = generate_embedding(tracks)
            embedding_count = sum(1 for t in tracks if t.get("embedding"))
            self.log(f"{embedding_count} embeddings generated - {embedding_count} embeddings générés")
        except Exception as e:
            self.log(f"Error generating embeddings: {str(e)} - Erreur lors de la génération des embeddings: {str(e)}")
            return None, None, None
        
        # Filter tracks with valid embeddings
        valid_tracks = [t for t in tracks if t.get("embedding")]
        
        if len(valid_tracks) < 2:
            self.log("Not enough songs with embeddings to build index. - Pas assez de chansons avec embeddings pour construire l'index.")
            return None, None, None
        
        # Step 6: Build FAISS index
        self.log("Building FAISS index... - Construction de l'index FAISS...")
        try:
            embeddings = np.array([t["embedding"] for t in valid_tracks]).astype("float32")
            index = build_faiss_index(embeddings)
            self.log(f"FAISS index built with {len(valid_tracks)} vectors - Index FAISS construit avec {len(valid_tracks)} vecteurs")
        except Exception as e:
            self.log(f"Error building index: {str(e)} - Erreur lors de la construction de l'index: {str(e)}")
            return None, None, None
        
        # Step 7: Search for similar songs
        # Use the first song (seed) as the query
        self.log("Searching for similar songs... - Recherche de chansons similaires...")
        try:
            seed_vector = np.array([valid_tracks[0]["embedding"]]).astype("float32")
            distances, indices = search_similar_songs(index, seed_vector[0], k=min(5, len(valid_tracks)-1))
            
            self.log(f"{len(indices[0])} similar songs found - {len(indices[0])} chansons similaires trouvées")
            self.log("Pipeline completed successfully! - Pipeline terminé avec succès!")
            
            if return_youtube_tracks:
                return {
                    "youtube_tracks": youtube_tracks,
                    "tracks_with_lyrics": tracks_with_lyrics,
                    "final_tracks": valid_tracks,
                    "distances": distances,
                    "indices": indices
                }
            return valid_tracks, distances, indices
            
        except Exception as e:
            self.log(f"Error during similarity search: {str(e)} - Erreur lors de la recherche de similarité: {str(e)}")
            if return_youtube_tracks:
                return {"youtube_tracks": youtube_tracks, "final_tracks": None, "distances": None, "indices": None}
            return None, None, None


def run_pipeline_standalone(query, limit=10, save_results=False):
    """
    Standalone function to run the pipeline outside of Streamlit.
    
    This function can be used for batch processing or testing purposes.
    
    Args:
        query: Search query string
        limit: Maximum number of songs to process (default: 10)
        save_results: If True, saves results to JSON file (default: False)
        
    Returns:
        dict: Dictionary containing:
            - tracks: List of processed songs
            - distances: Similarity scores
            - indices: Song indices
            - success: Boolean indicating pipeline success
    """
    import json
    import os
    from datetime import datetime
    
    pipeline = MusicPipeline()
    tracks, distances, indices = pipeline.run(query, limit)
    
    result = {
        "query": query,
        "timestamp": datetime.now().isoformat(),
        "success": tracks is not None,
        "tracks": tracks,
        "distances": distances.tolist() if distances is not None else None,
        "indices": indices.tolist() if indices is not None else None
    }
    
    if save_results and tracks:
        # Save to docs directory
        os.makedirs("docs", exist_ok=True)
        filename = f"docs/pipeline_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Résultats sauvegardés dans: {filename}")
    
    return result


if __name__ == "__main__":
    """
    Example usage when running the module directly.
    """
    import sys
    
    # Get query from command line or use default
    query = sys.argv[1] if len(sys.argv) > 1 else "Bohemian Rhapsody Queen"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    print(f"\n{'='*60}")
    print(f"🎵 Music Recommendation Pipeline")
    print(f"{'='*60}")
    print(f"Query: {query}")
    print(f"Limit: {limit}")
    print(f"{'='*60}\n")
    
    result = run_pipeline_standalone(query, limit, save_results=True)
    
    if result["success"]:
        print(f"\n✅ Pipeline exécuté avec succès!")
        print(f"📊 {len(result['tracks'])} chansons traitées")
    else:
        print(f"\n❌ Le pipeline a échoué.")
