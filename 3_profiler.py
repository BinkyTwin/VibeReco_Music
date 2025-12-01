import os
from openai import OpenAI
import json
from dotenv import load_dotenv

load_dotenv()

openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

with open("docs/candidate_list_with_lyrics.json", "r") as f:
    playlist = json.load(f)

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=openrouter_api_key,
)

def analyze_lyrics(artist, title, lyrics):
    completion = client.chat.completions.create(
    model="tngtech/deepseek-r1t2-chimera:free",
    messages=[
        {
        "role": "system",
        "content": """Tu es un expert en musicologie et psychologie. Analyse les paroles fournies pour extraire un profil émotionnel et sémantique structuré.
                        IMPORTANT : Ne donne pas d'explications, uniquement un objet JSON valide.

                        Format de sortie attendu (JSON) :
                        {
                        "song_meta": {
                            "title": "Titre",
                            "artist": "Artiste"
                            "language": "Langue"
                        },
                        "emotional_profile": {
                            "valence": "Float entre -1 (Négatif) et 1 (Positif)",
                            "arousal": "Float entre 0 (Calme) et 1 (Intense)",
                            "dominance": "Float entre 0 (Subi) et 1 (Contrôlé)",
                            "emotional_trajectory": "Description courte de l'évolution émotionnelle (ex: Triste -> Espoir)"
                        },
                        "semantic_layer": {
                            "primary_theme": "Thème principal (ex: Amour, Perte, Révolte...)",
                            "secondary_themes": ["Thème 2", "Thème 3"],
                            "keywords": ["mot1", "mot2", "mot3", "mot4", "mot5"],
                            "narrative_arc": "Résumé en une phrase de l'histoire racontée"
                        },
                        "contextual_metadata": {
                            "listening_context": ["Moment idéal pour écouter (ex: Soirée, Sport, Déprime)"],
                            "similarity_anchors": "Noms de 1 ou 2 artistes/chansons connus avec une vibe similaire"
                        }
                        }
                        CRITICAL: Output ONLY valid JSON. No explanation, no markdown, no preamble.
                        Never write: "Here is the JSON..." or "```
                        Start directly with: {
                        End directly with: }
                        """
        },
        {
        "role": "user",
        "content":f"Est-ce que tu peux analyser les paroles suivantes : \n {lyrics}, pour l'artiste suivant : \n {artist}, et le titre suivant : \n {title} ?"
        }
    ],
    response_format={'type': 'json_object'}
    )
    try:
        return json.loads(completion.choices[0].message.content)
    except json.JSONDecodeError:
        print(f"⚠️ Erreur de décodage JSON pour {title}")
        return None


for song in playlist:
    if song.get("lyrics"):
        analyse = analyze_lyrics(song["artist"], song["title"], song["lyrics"])
        song["analysis"] = analyse
    else:
        print(f"⚠️ Chanson sans paroles : {song['title']} - {song['artist']}")

with open("docs/candidates_analyzed.json", "w") as f:
    json.dump(playlist, f, indent=4, ensure_ascii=False)
    print("Chansons analysées et sauvegardées dans candidates_analyzed.json")

     

    