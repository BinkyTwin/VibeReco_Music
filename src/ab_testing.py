import json
import os
import random
import uuid
from datetime import datetime
import pandas as pd

RESULTS_FILE = os.path.join("data", "ab_test_results.json")

class ABTestManager:
    def __init__(self):
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        if not os.path.exists("data"):
            os.makedirs("data")
        if not os.path.exists(RESULTS_FILE):
            with open(RESULTS_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)

    def prepare_blind_test(self, youtube_tracks, vibe_tracks):
        """
        Randomly assigns playlists to A or B.
        Returns:
            dict: {
                "test_id": str,
                "A": list_of_tracks,
                "B": list_of_tracks,
                "mapping": {"A": "youtube" or "vibe", "B": "youtube" or "vibe"}
            }
        """
        test_id = str(uuid.uuid4())
        
        # Random flip
        if random.random() > 0.5:
            mapping = {"A": "youtube", "B": "vibe"}
            playlist_a = youtube_tracks
            playlist_b = vibe_tracks
        else:
            mapping = {"A": "vibe", "B": "youtube"}
            playlist_a = vibe_tracks
            playlist_b = youtube_tracks
            
        return {
            "test_id": test_id,
            "A": playlist_a,
            "B": playlist_b,
            "mapping": mapping,
            "timestamp": datetime.now().isoformat()
        }

    def save_vote(self, test_data, user_vote, numerical_scores, seed_song):
        """
        Saves the vote results.
        
        Args:
            test_data (dict): The object returned by prepare_blind_test
            user_vote (str): "A" or "B"
            numerical_scores (dict): Dictionary of scores (e.g. {'emotional': 4, ...})
            seed_song (str): Title of the seed song
        """
        # Determine who won: VibeReco or YouTube?
        winner_source = test_data["mapping"][user_vote]
        loser_source = test_data["mapping"]["B" if user_vote == "A" else "A"]
        
        record = {
            "test_id": test_data["test_id"],
            "timestamp": datetime.now().isoformat(),
            "seed_song": seed_song,
            "vote_for_playlist": user_vote,
            "winner_source": winner_source,  # "vibe" or "youtube"
            "scores": numerical_scores,
            "mapping": test_data["mapping"]
        }
        
        # Load existing
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError:
                history = []
        
        history.append(record)
        
        with open(RESULTS_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
            
        return True

    def get_stats(self):
        """
        Computes aggregate statistics.
        """
        if not os.path.exists(RESULTS_FILE):
            return None
        
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except:
                return None
                
        if not data:
            return None
            
        df = pd.DataFrame(data)
        
        total_votes = len(df)
        vibe_wins = len(df[df["winner_source"] == "vibe"])
        youtube_wins = len(df[df["winner_source"] == "youtube"])
        
        win_rate_vibe = (vibe_wins / total_votes) * 100 if total_votes > 0 else 0
        
        return {
            "total_votes": total_votes,
            "vibe_wins": vibe_wins,
            "youtube_wins": youtube_wins,
            "vibe_win_rate": win_rate_vibe
        }
