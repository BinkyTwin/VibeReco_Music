import os
import json
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as mtick
from datetime import datetime

# --- CONFIGURATION ---
# Load env vars manually if not in env
def load_env():
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, val = line.strip().split("=", 1)
                    # Strip quotes if present
                    val = val.strip('"').strip("'")
                    os.environ[key] = val

load_env()

KV_URL = os.environ.get("KV_REST_API_URL")
KV_TOKEN = os.environ.get("KV_REST_API_TOKEN")

OUTPUT_DIR = "analysis_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Set visual style
sns.set_theme(style="whitegrid")
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
COLOR_VIBE = "#8A2BE2"  # BlueViolet
COLOR_YOUTUBE = "#FF0000"  # Red
PALETTE = {"vibe": COLOR_VIBE, "youtube": COLOR_YOUTUBE}

def fetch_data():
    """Fetch all votes from Redis list 'vibereco:votes'"""
    print("Fetching data from Redis...")
    if not KV_URL or not KV_TOKEN:
        raise ValueError("Missing KV_REST_API_URL or KV_REST_API_TOKEN")

    # lrange vibereco:votes 0 -1
    url = f"{KV_URL}/lrange/vibereco:votes/0/-1"
    headers = {"Authorization": f"Bearer {KV_TOKEN}"}
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    data = response.json()
    raw_list = data.get("result", [])
    
    parsed_data = []
    print(f"Raw list type: {type(raw_list)}")
    if raw_list:
        print(f"First item type: {type(raw_list[0])}")
        print(f"First item: {raw_list[0]}")

    for item in raw_list:
        try:
            # Handle potential double encoding or non-string
            if isinstance(item, str):
                obj = json.loads(item)
            else:
                obj = item
                
            # If it's still a string (double encoded), try again
            if isinstance(obj, str):
                try:
                    obj = json.loads(obj)
                except:
                    pass
            
            if isinstance(obj, dict):
                parsed_data.append(obj)
            else:
                print(f"Skipping non-dict item: {obj}")
                
        except Exception as e:
            print(f"Error parsing item: {e}")
            continue
            
    df = pd.DataFrame(parsed_data)
    print(f"Loaded {len(df)} votes.")
    print("Columns:", df.columns.tolist())
    return df

def viz_win_rate_donut(df):
    """1. Global Win Rate Donut"""
    if 'winnerSource' not in df.columns:
        print("Column 'winnerSource' missing. Available:", df.columns.tolist())
        return
    plt.figure(figsize=(6, 6))
    
    counts = df['winnerSource'].value_counts()
    vibe_wins = counts.get('vibe', 0)
    total = len(df)
    vibe_pct = (vibe_wins / total) * 100 if total > 0 else 0
    yt_pct = 100 - vibe_pct
    
    labels = ['VibeReco', 'YouTube']
    sizes = [vibe_pct, yt_pct]
    colors = [COLOR_VIBE, COLOR_YOUTUBE]
    
    # Create donut
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.0f%%', startangle=90, pctdistance=0.85, wedgeprops=dict(width=0.3))
    
    # Central text
    center_circle = plt.Circle((0,0),0.70,fc='white')
    fig = plt.gcf()
    fig.gca().add_artist(center_circle)
    
    plt.text(0, 0, f"{int(vibe_pct)}%", ha='center', va='center', fontsize=24, fontweight='bold', color=COLOR_VIBE)
    plt.text(0, -0.2, "Preferred", ha='center', va='center', fontsize=10, color='gray')
    
    plt.title("VibeReco Win Rate", fontsize=14, pad=20)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/1_win_rate_donut.png", dpi=300)
    plt.close()
    print("Generated 1_win_rate_donut.png")

def viz_criteria_gains(df):
    """2. Average Gain per Criterion"""
    # Extract scores
    # Structure of 'scores': {'emotional': X, 'narrative': Y, 'keepability': Z}
    # We need to know the scores of the WINNER (which we have)
    # BUT we assume the user rates the PAIR? No, the user rates the playlists AFTER choosing?
    # Actually, looking at app.js: user chooses A or B, THEN rates THE CHOSEN ONE.
    # So we don't have the score for the loser. We can only compare Average Score of VibeReco Winners vs Average Score of YouTube Winners.
    # OR if the user rated both, we would compare paired.
    # Re-reading app.js: "scores" object is submitted with the vote. The user rates the chosen playlist.
    # So we compare Avg Score when Vibe Wins vs Avg Score when YouTube Wins.
    
    score_cols = ['emotional', 'narrative', 'keepability']
    
    # Expand scores column
    scores_df = df['scores'].apply(pd.Series)
    df_scores = pd.concat([df[['winnerSource']], scores_df], axis=1)
    
    # Calculate means
    means = df_scores.groupby('winnerSource')[score_cols].mean()
    
    if 'vibe' not in means.index or 'youtube' not in means.index:
        print("Not enough data for comparison (missing Vibe or YouTube wins).")
        return

    diffs = means.loc['vibe'] - means.loc['youtube'] # Positive = Vibe is better
    
    plt.figure(figsize=(8, 5))
    
    # Plot bars
    bars = plt.bar(diffs.index, diffs.values, color=['green' if x > 0 else 'red' for x in diffs.values])
    
    plt.axhline(0, color='black', linewidth=0.8)
    plt.ylabel("Score Difference (VibeReco - YouTube)")
    plt.title("Gain by Criterion (VibeReco vs YouTube Baseline)", pad=20)
    plt.ylim(min(diffs.min(), -1), max(diffs.max(), 1)) # Center somewhat
    
    # Labels
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                 f'{height:+.1f}',
                 ha='center', va='bottom' if height > 0 else 'top')

    # X labels
    labels_map = {
        'emotional': 'Cohérence Vibe',
        'narrative': 'Fluidité',
        'keepability': 'Envie de garder'
    }
    plt.xticks(range(len(diffs)), [labels_map.get(x, x) for x in diffs.index])
    
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/2_criteria_gain_bar.png", dpi=300)
    plt.close()
    print("Generated 2_criteria_gain_bar.png")

def viz_win_rate_by_seed(df):
    """3. Win Rate by Seed"""
    if 'seedTitle' not in df.columns:
        return

    # Calculate win rate per seed
    seeds = df.groupby('seedTitle')['winnerSource'].apply(lambda x: (x == 'vibe').mean() * 100).sort_values(ascending=True)
    
    plt.figure(figsize=(10, len(seeds) * 0.5 + 2))
    
    # Filter only seeds with > 1 vote to reduce noise? Optional. keeping all for now.
    
    bars = plt.barh(seeds.index, seeds.values, color=COLOR_VIBE)
    
    plt.xlim(0, 100)
    plt.xlabel("Win Rate (%)")
    plt.title("VibeReco Performance by Seed Song")
    
    # Add value labels
    for i, v in enumerate(seeds.values):
        plt.text(v + 1, i, f"{v:.0f}%", va='center')
        
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/3_win_rate_by_seed.png", dpi=300)
    plt.close()
    print("Generated 3_win_rate_by_seed.png")

def viz_playlist_changes(df):
    """4. Playlist Rank Changes (Bump Chart) - Simpler version: just a placeholder if we don't have track data"""
    # We only have vote data here, not the full playlists content (tracks) of each test.
    # The 'scores' component and 'ab_test_app.py' logic implies we SAVE the vote, but maybe not the full playlist detail?
    # checking app.js: voteData sends "winnerSource", "scores", "seedId"...
    # It DOES NOT seem to send the full list of tracks or their order.
    # So we CANNOT generate the "Before/After" bump chart from the VOTES alone.
    # We would need to generate it from the Algorithm for a specific seed.
    # I will create a static example generation for a known seed if possible, or skip this if data is missing.
    # For now, I will assume we can't do this from *votes* alone. 
    # BUT, the user asked for it. 
    # I will simulate it or note that we need to run the pipeline. 
    # Better: I will create a "Representative" bump chart by running the pipeline for the TOP performing seed.
    # But I can't easily run the full pipeline here without more deps (FAISS, etc).
    # I will skip this one for the script to valid "votes" but I will mention it.
    pass

def viz_score_distributions(df):
    """5. Score Distributions (Boxplot)"""
    score_cols = ['emotional', 'narrative', 'keepability']
    scores_df = df['scores'].apply(pd.Series)
    df_scores = pd.concat([df[['winnerSource']], scores_df], axis=1)
    
    # Melt for seaborn
    melted = df_scores.melt(id_vars='winnerSource', value_vars=score_cols, var_name='Criterion', value_name='Score')
    
    plt.figure(figsize=(10, 6))
    
    sns.boxplot(data=melted, x='Criterion', y='Score', hue='winnerSource', palette=PALETTE)
    
    plt.title("Distribution of Scores: VibeReco vs YouTube")
    plt.ylim(1, 5.5)
    plt.ylabel("User Rating (1-5)")
    
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/5_score_distribution.png", dpi=300)
    plt.close()
    print("Generated 5_score_distribution.png")

def main():
    try:
        df = fetch_data()
        
        if len(df) == 0:
            print("No data found.")
            return

        viz_win_rate_donut(df)
        viz_criteria_gains(df)
        viz_win_rate_by_seed(df)
        # viz_playlist_changes(df) # Requires track data
        viz_score_distributions(df)
        
        print("\nAnalysis complete. Charts saved to 'analysis_results/'.")
        
        # Print summary stats
        print("\n--- Summary ---")
        print(f"Total Votes: {len(df)}")
        print(df['winnerSource'].value_counts(normalize=True))
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
