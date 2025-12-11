"""
Pre-generate playlist pairs for all 15 seed songs.
This script runs the MusicPipeline for each seed and saves both:
- YouTube original order
- VibeReco reranked order

Output: data/ab_test_playlists.json

FEATURES:
- Incremental saves after each seed (no data loss on crash)
- Resume from existing data
- Converts numpy types to native Python for JSON
"""

import json
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pipeline import MusicPipeline
import numpy as np

# Official benchmark seedset
SEED_SONGS = [
    {"id": 1, "title": "Melodrama", "artist": "Disiz, Theodora", "query": "Melodrama Disiz Theodora", "vibe": "introspection"},
    {"id": 2, "title": "DIPLOMATICO", "artist": "ELGRANDETOTO", "query": "DIPLOMATICO ELGRANDETOTO", "vibe": "ego"},
    {"id": 3, "title": "LOVE YOU", "artist": "Nono La Grinta", "query": "LOVE YOU Nono La Grinta", "vibe": "amour"},
    {"id": 4, "title": "Génération Impolie", "artist": "Franglish, KeBlack", "query": "Génération Impolie Franglish KeBlack", "vibe": "fête"},
    {"id": 5, "title": "PARISIENNE", "artist": "GIMS, La Mano 1.9", "query": "PARISIENNE GIMS La Mano 1.9", "vibe": "night_drive"},
    {"id": 6, "title": "The Fate of Ophelia", "artist": "Taylor Swift", "query": "The Fate of Ophelia Taylor Swift", "vibe": "storytelling"},
    {"id": 7, "title": "ZOU BISOU", "artist": "Theodora, Jul", "query": "ZOU BISOU Theodora Jul", "vibe": "amour"},
    {"id": 8, "title": "BIRDS OF A FEATHER", "artist": "Billie Eilish", "query": "BIRDS OF A FEATHER Billie Eilish", "vibe": "introspection"},
    {"id": 9, "title": "Biff pas d'love", "artist": "Bouss", "query": "Biff pas d'love Bouss", "vibe": "rupture"},
    {"id": 10, "title": "RUINART", "artist": "R2", "query": "RUINART R2", "vibe": "ego"},
    {"id": 11, "title": "FASHION DESIGNA", "artist": "Theodora", "query": "FASHION DESIGNA Theodora", "vibe": "ego"},
    {"id": 12, "title": "CARTIER SANTOS", "artist": "SDM", "query": "CARTIER SANTOS SDM", "vibe": "ego"},
    {"id": 13, "title": "Disfruto", "artist": "Carla Morrison", "query": "Disfruto Carla Morrison", "vibe": "nostalgie"},
    {"id": 14, "title": "Nostalgique", "artist": "Jul", "query": "Nostalgique Jul", "vibe": "nostalgie"},
    {"id": 15, "title": "Iris", "artist": "The Goo Goo Dolls", "query": "Iris The Goo Goo Dolls", "vibe": "emotionnel"},
]

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "ab_test_playlists.json")


def to_native_type(value):
    """Convert numpy types to native Python types for JSON serialization."""
    if isinstance(value, (np.floating, np.float32, np.float64)):
        return float(value)
    elif isinstance(value, (np.integer, np.int32, np.int64)):
        return int(value)
    elif isinstance(value, np.ndarray):
        return value.tolist()
    return value


def format_track(track, index):
    """Format track for frontend display."""
    return {
        "position": index + 1,
        "title": track.get("title", "Unknown"),
        "artist": track.get("artist", "Unknown"),
        "videoId": track.get("videoId", ""),
        "vibeScore": 0,  # Will be set later with proper conversion
    }


def load_existing_data():
    """Load existing data to resume from previous run."""
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                print(f"📂 Loaded existing data with {len(data.get('playlists', {}))} seeds")
                return data
        except Exception as e:
            print(f"⚠️ Could not load existing data: {e}")
    return None


def save_data(data):
    """Save data to JSON file (incremental save)."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 Saved to {OUTPUT_FILE}")


def generate_playlist_pair(seed, limit=15):
    """
    Generate YouTube and VibeReco playlists for a single seed.
    
    Returns dict with:
    - youtube: list of tracks in YouTube order
    - vibereco: list of tracks reranked by VibeReco
    """
    print(f"\n{'='*60}")
    print(f"Processing seed: {seed['title']} - {seed['artist']}")
    print(f"{'='*60}")
    
    pipeline = MusicPipeline()
    
    try:
        results = pipeline.run(seed["query"], limit=limit, return_youtube_tracks=True)
        
        if not results or not results.get("final_tracks"):
            print(f"❌ Failed to get results for {seed['title']}")
            return None
        
        youtube_tracks = results["youtube_tracks"]
        vibe_tracks = results["final_tracks"]
        distances = results["distances"]
        indices = results["indices"]
        
        # YouTube order (original)
        youtube_playlist = [
            format_track(track, i) 
            for i, track in enumerate(youtube_tracks)
        ]
        
        # VibeReco order (reranked by similarity)
        if indices is not None and len(indices) > 0:
            vibe_order_indices = indices[0]
            vibereco_playlist = []
            for i, idx in enumerate(vibe_order_indices):
                if idx < len(vibe_tracks):
                    track = vibe_tracks[idx]
                    distance = distances[0][i] if distances is not None else 0
                    formatted = format_track(track, i)
                    # Convert numpy float32 to native Python float
                    vibe_score = 1 - distance if distance < 1 else 0
                    formatted["vibeScore"] = round(float(vibe_score), 3)
                    vibereco_playlist.append(formatted)
        else:
            vibereco_playlist = youtube_playlist
        
        return {
            "youtube": youtube_playlist[:limit],
            "vibereco": vibereco_playlist[:limit]
        }
        
    except Exception as e:
        print(f"❌ Error processing {seed['title']}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Generate all playlist pairs and save to JSON."""
    print("\n" + "="*70)
    print(" VibeReco A/B Test - Playlist Pre-Generation")
    print(" (with incremental saves - crash-resistant)")
    print("="*70)
    
    # Try to load existing data to resume
    existing_data = load_existing_data()
    
    if existing_data:
        all_playlists = existing_data
        print(f"🔄 Resuming from existing data...")
    else:
        all_playlists = {
            "generated_at": datetime.now().isoformat(),
            "seeds": SEED_SONGS,
            "playlists": {}
        }
    
    success_count = 0
    skipped_count = 0
    
    for seed in SEED_SONGS:
        seed_id = str(seed["id"])
        
        # Skip if already processed successfully
        if seed_id in all_playlists["playlists"] and all_playlists["playlists"][seed_id] is not None:
            print(f"\n⏭️  Skipping {seed['title']} (already processed)")
            skipped_count += 1
            success_count += 1
            continue
        
        result = generate_playlist_pair(seed)
        
        if result:
            all_playlists["playlists"][seed_id] = result
            success_count += 1
            print(f"✅ {seed['title']}: {len(result['youtube'])} tracks (YT) / {len(result['vibereco'])} tracks (VR)")
        else:
            all_playlists["playlists"][seed_id] = None
        
        # INCREMENTAL SAVE after each seed
        all_playlists["last_updated"] = datetime.now().isoformat()
        save_data(all_playlists)
    
    print(f"\n{'='*70}")
    print(f"✅ Generation complete: {success_count}/{len(SEED_SONGS)} seeds processed")
    if skipped_count > 0:
        print(f"⏭️  {skipped_count} seeds were already processed (skipped)")
    print(f"📁 Output saved to: {OUTPUT_FILE}")
    print(f"{'='*70}\n")
    
    return all_playlists


if __name__ == "__main__":
    main()
