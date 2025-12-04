from openai import OpenAI
from src.config import OPENROUTER_API_KEY

def analyze_emotional_profile(lyrics_text):
    """
    Analyzes song lyrics to extract a structured emotional and semantic profile using AI.
    
    This function uses OpenRouter's AI model to analyze lyrics and generate a comprehensive
    profile including emotional dimensions (valence, arousal, dominance), semantic themes,
    and contextual metadata for music recommendation purposes.
    
    Args:
        lyrics_text: String containing the song lyrics to analyze
        
    Returns:
        dict: A structured JSON object containing:
            - song_meta: Title, artist, and language information
            - emotional_profile: Valence, arousal, dominance scores and emotional trajectory
            - semantic_layer: Primary/secondary themes, keywords, and narrative arc
            - contextual_metadata: Listening contexts and similarity anchors
        None: If JSON decoding fails
        
    Raises:
        May print warning message if JSON decoding fails
    """

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )

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
        json_profile = json.loads(completion.choices[0].message.content)
        return json_profile
    except json.JSONDecodeError:
        print(f"⚠️ Erreur de décodage JSON pour {title}")
        return None

def generate_vibe_text(song_data):
    for song in song_data:
        if song.get("analysis"):
            data = song["analysis"]

            theme_str = "".join(data["semantic_layer"]["primary_theme"])
            secondary_themes_str = ", ".join(data["semantic_layer"]["secondary_themes"])
            keywords_str = ", ".join(data["semantic_layer"]["keywords"])
            context_str = ", ".join(data["contextual_metadata"]["listening_context"])
            vibe_string = (
            f"Title: {song['title']}. Artist: {song['artist']}. "
            f"Primary Theme: {theme_str}. "
            f"Secondary Themes: {secondary_themes_str}. "
            f"Emotions: Valence {data['emotional_profile']['valence']}, "
            f"Arousal {data['emotional_profile']['arousal']}, "
            f"Dominance {data['emotional_profile']['dominance']}. "
            f"Vibe Description: {data['emotional_profile']['emotional_trajectory']}. "
            f"Keywords: {keywords_str}. "
            f"Context: {context_str}. "
            f"Narrative: {data['semantic_layer']['narrative_arc']}"
            )

            song["vibe_text"] = vibe_string
            print(f"Vibe text generated for {song['title']} by {song['artist']}")

        else:
            song["vibe_text"] = None
            print(f"Vibe text not generated for {song['title']} by {song['artist']}")
    return vibe_string

        
