# README (English)

## Overview

This project is an **LLM-powered music recommendation system** that focuses on the **emotional and semantic content of lyrics**, rather than only on audio features or collaborative filtering.

Given a seed song (via YouTube Music), the system:

- retrieves similar tracks from **YouTube Music**  
- fetches **lyrics** from YouTube Music and falls back to **Genius**  
- uses a **Large Language Model (DeepSeek R1T2 Chimera via OpenRouter)** to extract a structured **emotional + semantic profile** from the lyrics  
- converts this profile into a compact **“vibe text”** description  
- embeds these vibe texts using **OpenAI text-embedding-3-small**  
- builds a **FAISS** index and performs **similarity search** to recommend tracks with a similar emotional/thematic “vibe”.

The goal is to build a recommendation system that is closer to how humans actually experience songs: not only via audio mood (happy/sad, energetic/calm), but also via **themes, narratives, and listening context** (breakup songs, protest songs, comforting songs, etc.).

***

## Research Foundations

This project is based on two main research axes:

1. **Emotion modeling in music (VAD / Russell)**
2. **Hybrid emotion + semantic understanding via LLMs**

### 1. Emotion Modeling: Valence–Arousal–Dominance (VAD)

The **emotional profile** extracted from lyrics is inspired by the **Valence–Arousal–Dominance** framework, widely used in **Music Emotion Recognition (MER)** and affective computing:

- **Valence**: emotional polarity (negative ↔ positive)  
- **Arousal**: activation/energy level (calm ↔ intense)  
- **Dominance**: sense of control (powerless ↔ in control)

This is directly related to:

- Russell’s **circumplex model of affect** (Valence–Arousal)
- The extended **VAD model** used in affective lexicons and recent music emotion work  
- Surveys and works in multimodal MER showing that VA or VAD coordinates are a de facto **gold standard** for representing musical emotions in a continuous space.

In the code, these dimensions are captured in the `emotional_profile` section returned by the LLM.

### 2. Beyond Numbers: Semantic Themes and Narrative

Literature shows that **emotion coordinates alone are not enough** to capture how humans perceive the *meaning* of songs. Two songs can share a similar VAD profile (e.g. negative, intense, low control) but talk about very different topics:

- a devastating breakup  
- fear of war  

For recommendation, these should **not** always be treated as interchangeable.

Recent work in **hybrid music recommendation** and **LLM-based emotion-aware systems** emphasizes combining:

- low-level emotion dimensions (VAD, mood)
- high-level **semantic information**:
  - primary theme (love, loss, social struggle, nostalgia, etc.)
  - secondary themes
  - narrative arc (how the story evolves)
  - contextual usage (when/why someone would listen to this song)

This project follows that direction:

- The LLM returns a **structured JSON profile** with:
  - `emotional_profile`: VAD + emotional trajectory  
  - `semantic_layer`: primary theme, secondary themes, keywords, narrative arc  
  - `contextual_metadata`: listening contexts and similarity anchors (artists/songs with a similar vibe)

- A second step (`generate_vibe_text`) converts this structured profile into a **dense natural language description** (“vibe text”) that captures both emotional state and themes.  
- These vibe texts are then embedded and used as the basis for vector similarity.

This design is inspired by recent work where **LLMs act as high-level feature extractors**, enriching traditional MIR features with human-like descriptors and context.

***

## Architecture

The code is organized into clear modules under `src/`:

### 1. `config.py`

Centralized configuration and environment handling:

- Loads API keys and settings from `.env`:
  - `OPENAI_API_KEY` – for embeddings (text-embedding-3-small)
  - `OPENROUTER_API_KEY` – for LLM analysis (DeepSeek R1T2 Chimera)
  - `TOKEN_GENIUS`, `CLIENT_ID_GENIUS`, `CLIENT_SECRET_GENIUS` – for Genius lyrics API
- Defines `DATA_DIR` for storing local data.

### 2. `extraction.py`

Responsible for data acquisition:

- `get_youtube_recommendations(seed_query, limit=10)`  
  - Uses **ytmusicapi** to search YouTube Music for a seed query (song/artist)  
  - Builds a “radio” style playlist around the first matching track  
  - Returns a list of tracks with basic metadata: `title`, `artist`, `videoId`.

- `fetch_lyrics(tracks)`  
  - For each track:
    1. Tries to fetch lyrics directly from YouTube Music (when available)
    2. Falls back to **Genius** using `lyricsgenius`
  - Cleans noisy titles (e.g. `(Official Video)`) before querying Genius
  - Enriches each track with:
    - `lyrics`
    - `status` ("found"/"not found")
    - `source` ("ytmusic"/"genius")

### 3. `analysis.py`

Handles LLM-based emotional and semantic analysis:

- `analyze_emotional_profile(title, artist, lyrics)`  
  - Calls **OpenRouter** with the `tngtech/deepseek-r1t2-chimera:free` model  
  - Sends a carefully designed system prompt in French, instructing the model to output **only a valid JSON object** with the following structure:

    ```json
    {
      "song_meta": {
        "title": "Titre",
        "artist": "Artiste",
        "language": "Langue"
      },
      "emotional_profile": {
        "valence": ...,
        "arousal": ...,
        "dominance": ...,
        "emotional_trajectory": "..."
      },
      "semantic_layer": {
        "primary_theme": "...",
        "secondary_themes": ["..."],
        "keywords": ["..."],
        "narrative_arc": "..."
      },
      "contextual_metadata": {
        "listening_context": ["..."],
        "similarity_anchors": "..."
      }
    }
    ```

  - Uses `response_format={'type': 'json_object'}` to enforce JSON  
  - Returns the parsed dict or `None` if decoding fails.

- `generate_vibe_text(song_data)`  
  - For each analyzed song:
    - Extracts emotional and semantic fields from `analysis`
    - Builds a **vibe string** such as:

      > "Title: X. Artist: Y. Primary Theme: …. Secondary Themes: …. Emotions: Valence …, Arousal …, Dominance …. Vibe Description: …. Keywords: …. Context: …. Narrative: …"

    - Stores this as `song["vibe_text"]`

  - These vibe texts are used later for embeddings.

### 4. `recommendation.py`

Vectorization and similarity search:

- Initializes an OpenAI client with `text-embedding-3-small`.
- `generate_embedding(text_list)`  
  - For each song with a `vibe_text`:
    - Calls the embedding API
    - Stores the resulting vector under `song["embedding"]`.
- `build_faiss_index(vectors)`  
  - Builds a FAISS index (`IndexFlatIP`) on L2-normalized vectors
  - Inner product on normalized vectors ≈ cosine similarity.
- `search_similar_songs(index, query_vector, k=5)`  
  - Normalizes the query vector  
  - Returns the `k+1` nearest neighbors (including the query itself).

### 5. `pipeline.py`

High-level orchestration via the `MusicPipeline` class:

- `__init__(status_callback=None)`  
  - Optional callback (e.g. to integrate with a Streamlit UI) for logging status.

- `run(query, limit=10, return_youtube_tracks=False)`  
  - End-to-end workflow:
    1. Search YouTube Music (`get_youtube_recommendations`)
    2. Fetch lyrics (`fetch_lyrics`)
    3. Analyze emotional/semantic profiles (`analyze_emotional_profile`)
    4. Generate vibe texts (`generate_vibe_text`)
    5. Generate embeddings (`generate_embedding`)
    6. Build FAISS index (`build_faiss_index`)
    7. Search similar songs (`search_similar_songs`)

  - Returns either:
    - `(tracks, distances, indices)`  
    - or a dict with intermediate artifacts if `return_youtube_tracks=True`.

***

## Installation

```bash
git clone <your-repo-url>
cd <your-repo-folder>
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

`requirements.txt` includes:

- `streamlit`
- `openai`
- `ytmusicapi`
- `lyricsgenius`
- `faiss-cpu`
- `python-dotenv`
- `numpy`
- `pandas`
- `seaborn`
- `matplotlib`

***

## Configuration

Create a `.env` file at the project root:

```env
OPENAI_API_KEY=your_openai_key
OPENROUTER_API_KEY=your_openrouter_key
TOKEN_GENIUS=your_genius_token
CLIENT_ID_GENIUS=your_genius_client_id
CLIENT_SECRET_GENIUS=your_genius_client_secret
```

These values are loaded by `src/config.py`.

***

## Usage

Example (Python):

```python
from src.pipeline import MusicPipeline

pipeline = MusicPipeline()

tracks, distances, indices = pipeline.run(
    query="Stand By Me Ben E. King",
    limit=10
)

# tracks[i] contains:
# - YouTube metadata
# - lyrics
# - emotional/semantic analysis
# - vibe_text
# - embedding
```

You can then use `tracks`, `distances`, and `indices` to display recommendations, build a UI, or run further analysis.

***

## Limitations and Future Work

- Depends on third-party APIs (YouTube Music, Genius, OpenRouter, OpenAI) → subject to rate limits and changes.
- Emotion recognition is **inferred** from lyrics only; no audio analysis is used yet.
- The LLM-based analysis is powerful but not perfect: it can sometimes misinterpret language nuances, slang, or multilingual lyrics.

Potential future extensions:

- Add audio features (tempo, energy, valence from Spotify/other MIR tools) to complement lyrics.
- Fine-tune a dedicated emotion model on annotated lyric datasets and compare to LLM-based zero/few-shot.
- Add user modeling (personal history, skip/like behavior) to refine recommendations.

***

## A/B Test Platform

The project includes a **blind A/B testing platform** to quantitatively evaluate VibeReco's reranking against YouTube's default recommendations.

### Purpose

Compare two playlists built from the same seed song:
- **Playlist A/B (randomized)**: YouTube's original recommendation order vs VibeReco's emotional coherence reranking
- Users don't know which is which → **unbiased evaluation**

### Architecture

```
ab_test/
├── index.html          # Main web interface
├── styles.css          # Premium dark-mode UI
├── app.js              # Frontend logic (player, voting, state management)
├── seeds.js            # Seed songs configuration
├── generate_playlists.py   # Pre-generates playlist pairs via MusicPipeline
├── api/
│   └── track.js        # Serverless endpoint for track streaming
└── data/
    └── ab_test_playlists.json  # Pre-computed playlist pairs
```

### How It Works

1. **Seed Selection** (Step 1): User picks a seed song from 15 curated tracks spanning different vibes (introspection, ego, love, party, etc.)

2. **Blind Comparison** (Step 2): Two playlists are displayed side-by-side, randomly assigned as A or B. User can listen to tracks from both playlists.

3. **Evaluation** (Step 3): User rates their preferred playlist on 3 criteria:
   - **Emotional coherence**: Are emotions consistent from track to track?
   - **Narrative coherence**: Is there a progression, a thread?
   - **Keepability**: Would you save this playlist for later?

4. **Vote Submission**: Results are stored in Redis (via Upstash) for analysis.

### Running the A/B Test

**1. Generate playlist data:**

```bash
cd ab_test
python generate_playlists.py
```

This runs the MusicPipeline for all 15 seeds and saves both orderings to `data/ab_test_playlists.json`.

**2. Serve locally:**

```bash
# Using Python's built-in server
python -m http.server 8000 --directory ab_test

# Or use any static file server
npx serve ab_test
```

**3. Deploy:**

The platform is designed for Vercel deployment with the serverless API endpoint.

### Evaluation Metrics

Results can be analyzed to compute:
- **Win rate**: % of votes where VibeReco was preferred
- **Score gain**: Average rating improvement vs YouTube
- **Win rate by vibe category**: Performance across different emotional contexts
- **Score distributions**: Boxplots comparing rating patterns

***

# README (Français)

## Vue d’ensemble

Ce projet est un **système de recommandation musicale piloté par LLM**, centré sur le **contenu émotionnel et sémantique des paroles**, plutôt que uniquement sur l’audio ou le collaboratif.

À partir d’une chanson de départ (via YouTube Music), le système :

- récupère des titres similaires depuis **YouTube Music**  
- obtient les **paroles** via YouTube Music, puis se rabat sur **Genius** si besoin  
- utilise un **Large Language Model (DeepSeek R1T2 Chimera via OpenRouter)** pour extraire un **profil émotionnel + sémantique structuré** à partir des paroles  
- transforme ce profil en une **“vibe description”** textuelle compacte  
- génère des embeddings de ces vibes via **OpenAI text-embedding-3-small**  
- construit un index **FAISS** et effectue une **recherche de similarité** pour recommander des chansons avec une vibe émotionnelle/thématique proche.

L’objectif est d’approcher la manière dont les humains vivent réellement la musique : non seulement par l’humeur sonore (joyeux/triste, calme/énergique), mais aussi par les **thèmes, les récits et le contexte d’écoute** (chansons de rupture, chansons engagées, morceaux réconfortants, etc.).

***

## Fondements théoriques

Le projet repose sur deux axes principaux :

1. **Modélisation des émotions musicales (VAD / Russell)**  
2. **Compréhension hybride émotion + sémantique via LLM**

### 1. Modélisation émotionnelle : Valence–Arousal–Dominance (VAD)

Le **profil émotionnel** extrait des paroles est inspiré du cadre **Valence–Arousal–Dominance**, très utilisé en **Music Emotion Recognition (MER)** et en informatique affective :

- **Valence** : polarité émotionnelle (négatif ↔ positif)  
- **Arousal** : niveau d’activation/énergie (calme ↔ intense)  
- **Dominance** : sentiment de contrôle (subi ↔ maîtrisé)

Cela se rattache directement :

- au **modèle circomplexe** de Russell (Valence–Arousal)  
- au modèle **VAD** étendu utilisé dans les lexiques affectifs et les travaux récents sur l’émotion musicale  
- aux revues en MER multimodal qui considèrent VA ou VAD comme un **standard de facto** pour représenter les émotions dans un espace continu.

Dans le code, ces dimensions sont capturées dans la section `emotional_profile` renvoyée par le LLM.

### 2. Au‑delà des chiffres : thèmes sémantiques et récit

La littérature montre que des **coordonnées émotionnelles** ne suffisent pas à rendre compte de la façon dont les humains perçoivent le *sens* d’une chanson. Deux titres peuvent partager un profil VAD similaire (ex. négatif, intense, faible contrôle) mais parler de choses très différentes :

- une rupture amoureuse dévastatrice  
- la peur de la guerre  

Pour la recommandation, ces chansons ne sont **pas toujours substituables**.

Les travaux récents sur les systèmes de recommandation “**émotion + sémantique**” et sur les approches LLM mettent en avant la combinaison :

- de dimensions émotionnelles continues (VAD, mood)
- avec des informations **sémantiques de haut niveau** :
  - thème principal (amour, perte, luttes sociales, nostalgie, etc.)
  - thèmes secondaires
  - arc narratif (évolution de l’histoire)
  - contexte d’usage (quand/pourquoi on écoute ce morceau)

Ce projet suit exactement cette approche :

- Le LLM renvoie un **JSON structuré** comprenant :
  - `emotional_profile` : VAD + trajectoire émotionnelle  
  - `semantic_layer` : thème principal, thèmes secondaires, mots-clés, arc narratif  
  - `contextual_metadata` : contextes d’écoute et artistes/morceaux de vibe proche

- Une seconde étape (`generate_vibe_text`) transforme ce profil structuré en une **description naturelle (“vibe text”)** qui résume à la fois l’état émotionnel et les thèmes.  
- Ces vibes sont ensuite **encodées en vecteurs** et utilisées comme base de la similarité.

Cette conception s’inspire des travaux où les **LLM servent d’extracteurs de features de haut niveau**, venant enrichir les descripteurs MIR classiques par des annotations proches du langage humain.

***

## Architecture

Le code est organisé en modules au sein de `src/` :

### 1. `config.py`

Module de configuration et de gestion des variables d’environnement :

- Charge les clés API et paramètres depuis `.env` :
  - `OPENAI_API_KEY` – embeddings (text-embedding-3-small)
  - `OPENROUTER_API_KEY` – analyse LLM (DeepSeek R1T2 Chimera)
  - `TOKEN_GENIUS`, `CLIENT_ID_GENIUS`, `CLIENT_SECRET_GENIUS` – API Genius pour les paroles
- Définit `DATA_DIR` pour le stockage local.

### 2. `extraction.py`

Responsable de l’acquisition des données :

- `get_youtube_recommendations(seed_query, limit=10)`  
  - Utilise **ytmusicapi** pour chercher la chanson de départ  
  - Construit une playlist “radio” autour de ce titre  
  - Retourne une liste de morceaux avec : `title`, `artist`, `videoId`.

- `fetch_lyrics(tracks)`  
  - Pour chaque morceau :
    1. Tente de récupérer les paroles via YouTube Music  
    2. Se rabat sur **Genius** via `lyricsgenius` si nécessaire
  - Nettoie les titres bruyants (ex. `(Official Video)`) avant d’interroger Genius  
  - Ajoute à chaque piste :
    - `lyrics`
    - `status` ("found"/"not found")
    - `source` ("ytmusic"/"genius")

### 3. `analysis.py`

Analyse émotionnelle et sémantique via LLM :

- `analyze_emotional_profile(title, artist, lyrics)`  
  - Appelle **OpenRouter** avec le modèle `tngtech/deepseek-r1t2-chimera:free`  
  - Utilise un prompt `system` en français qui impose la sortie sous forme d’un **objet JSON valide** avec :

    ```json
    {
      "song_meta": { ... },
      "emotional_profile": { ... },
      "semantic_layer": { ... },
      "contextual_metadata": { ... }
    }
    ```

  - Utilise `response_format={'type': 'json_object'}` pour renforcer le respect du JSON  
  - Parse la réponse et renvoie un dict, ou `None` en cas d’erreur de décodage.

- `generate_vibe_text(song_data)`  
  - Pour chaque chanson analysée :
    - Récupère les champs émotionnels et sémantiques
    - Construit une phrase décrivant la **vibe** (titre, artiste, thèmes, VAD, trajectoire, mots-clés, contexte, narration)
    - Stocke cette description dans `song["vibe_text"]`.

### 4. `recommendation.py`

Vectorisation et recommandation :

- Initialise un client OpenAI (`text-embedding-3-small`).
- `generate_embedding(text_list)`  
  - Pour chaque chanson avec un `vibe_text` :
    - Appelle l’API d’embedding  
    - Enregistre le vecteur sous `song["embedding"]`.
- `build_faiss_index(vectors)`  
  - Convertit la liste de vecteurs en `numpy`  
  - Normalise (L2) et construit un index FAISS `IndexFlatIP` (cosine après normalisation).
- `search_similar_songs(index, query_vector, k=5)`  
  - Normalise le vecteur requête  
  - Retourne les `k+1` voisins les plus proches.

### 5. `pipeline.py`

Orchestration haut niveau via `MusicPipeline` :

- `__init__(status_callback=None)`  
  - Callback optionnel pour afficher les logs (pratique pour une UI Streamlit).

- `run(query, limit=10, return_youtube_tracks=False)`  
  - Chaîne l’ensemble du pipeline :
    1. Recherche YouTube Music (`get_youtube_recommendations`)
    2. Récupération des paroles (`fetch_lyrics`)
    3. Analyse émotionnelle/sémantique via LLM (`analyze_emotional_profile`)
    4. Génération des vibe texts (`generate_vibe_text`)
    5. Embeddings (`generate_embedding`)
    6. Index FAISS (`build_faiss_index`)
    7. Recherche de similarité (`search_similar_songs`)

  - Retourne soit :
    - `(tracks, distances, indices)`  
    - soit un dict avec les étapes intermédiaires si `return_youtube_tracks=True`.

***

## Installation

```bash
git clone <url-de-votre-repo>
cd <dossier-du-projet>
python -m venv .venv
source .venv/bin/activate  # ou .venv\Scripts\activate sous Windows
pip install -r requirements.txt
```

`requirements.txt` contient notamment :

- `streamlit`
- `openai`
- `ytmusicapi`
- `lyricsgenius`
- `faiss-cpu`
- `python-dotenv`
- `numpy`
- `pandas`
- `seaborn`
- `matplotlib`

***

## Configuration

Créer un fichier `.env` à la racine :

```env
OPENAI_API_KEY=votre_cle_openai
OPENROUTER_API_KEY=votre_cle_openrouter
TOKEN_GENIUS=votre_token_genius
CLIENT_ID_GENIUS=votre_client_id_genius
CLIENT_SECRET_GENIUS=votre_client_secret_genius
```

Ces variables sont chargées dans `src/config.py`.

***

## Utilisation

Exemple simple (Python) :

```python
from src.pipeline import MusicPipeline

pipeline = MusicPipeline()

tracks, distances, indices = pipeline.run(
    query="Stand By Me Ben E. King",
    limit=10
)

# tracks[i] contient :
# - métadonnées YouTube
# - paroles
# - analyse émotionnelle/sémantique
# - vibe_text
# - embedding
```

Vous pouvez ensuite utiliser ces résultats pour construire une interface utilisateur, explorer les vibes, ou tester différentes stratégies de recommandation.

***

## Limites et pistes d’amélioration

- Forte dépendance aux APIs externes (YouTube Music, Genius, OpenRouter, OpenAI) → limites de quota, changements d’API possibles.
- L’émotion est **déduite uniquement des paroles** : aucun traitement audio n’est encore intégré.
- L’analyse via LLM, même avancée, peut se tromper sur certains registres (argot, multilingue, références culturelles).

Pistes futures :

- Ajouter des features audio (tempo, energy, valence audio) pour un MER vraiment multimodal.
- Entraîner/fine-tuner un modèle dédié sur des datasets annotés en émotion de paroles et comparer avec l’approche LLM.
- Introduire un modèle utilisateur (historique, likes, skips) pour personnaliser encore plus les recommandations.

***

## Plateforme de Test A/B

Le projet inclut une **plateforme de test A/B en aveugle** pour évaluer quantitativement le re-ranking VibeReco face aux recommandations par défaut de YouTube.

### Objectif

Comparer deux playlists construites à partir du même morceau seed :
- **Playlist A/B (randomisée)** : ordre original YouTube vs re-ranking par cohérence émotionnelle VibeReco
- L'utilisateur ne sait pas laquelle est laquelle → **évaluation non biaisée**

### Architecture

```
ab_test/
├── index.html          # Interface web principale
├── styles.css          # UI premium dark-mode
├── app.js              # Logique frontend (player, vote, gestion d'état)
├── seeds.js            # Configuration des morceaux seed
├── generate_playlists.py   # Pré-génère les paires de playlists via MusicPipeline
├── api/
│   └── track.js        # Endpoint serverless pour le streaming
└── data/
    └── ab_test_playlists.json  # Paires de playlists pré-calculées
```

### Fonctionnement

1. **Choix du seed** (Étape 1) : L'utilisateur choisit un morceau parmi 15 titres couvrant différentes vibes (introspection, ego, amour, fête, etc.)

2. **Comparaison à l'aveugle** (Étape 2) : Deux playlists côte à côte, assignées aléatoirement en A ou B. L'utilisateur peut écouter les morceaux des deux.

3. **Évaluation** (Étape 3) : L'utilisateur note sa playlist préférée sur 3 critères :
   - **Cohérence émotionnelle** : Les émotions sont-elles constantes d'un morceau à l'autre ?
   - **Cohérence narrative** : Y a-t-il une progression, un fil conducteur ?
   - **Envie de garder** : Enregistrerais-tu cette playlist pour plus tard ?

4. **Soumission** : Les votes sont stockés dans Redis (via Upstash) pour analyse.

### Lancer le test A/B

**1. Générer les données :**

```bash
cd ab_test
python generate_playlists.py
```

Cela exécute le MusicPipeline pour les 15 seeds et sauvegarde les deux ordres dans `data/ab_test_playlists.json`.

**2. Servir en local :**

```bash
# Avec le serveur intégré Python
python -m http.server 8000 --directory ab_test

# Ou n'importe quel serveur de fichiers statiques
npx serve ab_test
```

**3. Déployer :**

La plateforme est conçue pour un déploiement Vercel avec l'API serverless.

### Métriques d'évaluation

Les résultats permettent de calculer :
- **Taux de victoire** : % des votes où VibeReco a été préféré
- **Gain de score** : Amélioration moyenne des notes vs YouTube
- **Taux de victoire par catégorie de vibe** : Performance selon le contexte émotionnel
- **Distribution des scores** : Boxplots comparant les patterns de notation

[1](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/53429284/01d6b599-74ef-474c-9f57-740541b4e237/requirements.txt)
[2](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/53429284/12048261-1670-4100-a43f-c8fdeca1761b/pipeline.py)
[3](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/53429284/5148efca-a783-4f3d-ab32-3727a56ed123/config.py)
[4](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/53429284/f531d6ad-efda-4711-9738-d66e75c90959/extraction.py)
[5](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/53429284/089ce6a2-2b6a-4b8f-a832-06f3612c5929/recommendation.py)
[6](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/53429284/d5d739a8-945f-4a86-9c8d-0c985530012f/analysis.py)