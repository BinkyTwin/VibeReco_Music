import os
from openai import OpenAI
import json
from dotenv import load_dotenv

load_dotenv()

openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

with open("docs/candidates_analyzed.json", "r") as f:
    analyse_json = json.load(f)

for song in analyse_json:
    if song.get("analysis"):
        data = song["analysis"]

        theme_str = ", ".join(data["semantic_layer"]["primary_theme"])
        keywords_str = ", ".join(data["semantic_layer"]["keywords"])
        context_str = ", ".join(data["contextual_metadata"]["listening_context"])
        vibe_text = (
            f"Title: {song['title']}. Artist: {song['artist']}. "
            f"Primary Theme: {theme_str}. "
            f"Secondary Themes: {data['semantic_layer']['secondary_themes']}. "
            f"Emotions: Valence {data['emotional_profile']['valence']}, "
            f"Arousal {data['emotional_profile']['arousal']}, "
            f"Dominance {data['emotional_profile']['dominance']}. "
            f"Vibe Description: {data['emotional_profile']['emotional_trajectory']}. "
            f"Keywords: {keywords_str}. "
            f"Context: {context_str}. "
            f"Narrative: {data['semantic_layer']['narrative_arc']}"
        )

        song["vibe_text"] = vibe_text
        print(f"Vibe text generated for {song['title']} by {song['artist']}")

    else:
        song["vibe_text"] = f"Title: {song['title']}. Artist: {song['artist']}. Status: Instrumental or Lyrics not found"

with open("docs/candidates_with_vibe_text.json", "w") as f:
    json.dump(analyse_json, f, indent=4, ensure_ascii=False)
    print("All vibe text generated and saved in candidates_with_vibe_text.json")

