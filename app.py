import streamlit as st
import numpy as np
import os
import json
import faiss
from src.pipeline import MusicPipeline

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Deep Vibe Recommender",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STYLES CSS PERSONNALISÉS ---
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        color: #31333F;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border-left: 5px solid #ff4b4b;
    }
    .vibe-text {
        font-style: italic;
        color: #555;
        border-left: 3px solid #ccc;
        padding-left: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- FONCTIONS UTILITAIRES POUR LE MODE CATALOGUE (STATIC) ---
@st.cache_data
def load_static_data():
    path = os.path.join("data", "candidates_with_embedding.json")
    # Fallback pour compatibilité avec l'ancienne structure
    if not os.path.exists(path):
        path = "docs/candidates_with_embedding.json"
    
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

@st.cache_resource
def load_static_index():
    path = os.path.join("data", "my_music_index.faiss")
    # Fallback
    if not os.path.exists(path):
        path = "docs/my_music_index.faiss"
        
    if os.path.exists(path):
        return faiss.read_index(path)
    return None

# --- UI PRINCIPALE ---
def main():
    # En-tête avec explication du concept
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🎹 Deep Vibe Recommender")
        st.markdown("""
                ### More than just a playlist... an emotional connection.

        Most music recommendations are based on genre ("It's Rock") or listening history ("People who like X also like Y").

        **This project is different.** It uses LLMs to:
        1. **Read and understand** song lyrics in depth.
        2. Extract **the soul and emotion** (the "Vibe").
        3. Find other songs that share this **same emotional resonance**, regardless of musical style.

        ---
        
        ### Plus qu'une simple playlist... une connexion émotionnelle.
        
        La plupart des recommandations musicales se basent sur le genre ("C'est du Rock") ou sur l'historique d'écoute ("Les gens qui aiment X aiment aussi Y").
        
        **Ce projet est différent.** Il utilise des LLM's pour :
        1. **Lire et comprendre** les paroles d'une chanson en profondeur.
        2. En extraire **l'âme et l'émotion** (la "Vibe").
        3. Trouver d'autres chansons qui partagent cette **même résonance émotionnelle**, peu importe le style musical.

        ---


        """)
    
    with col2:
        st.image("https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=400&q=80", use_container_width=True)

    st.divider()

    tab_live, tab_static = st.tabs(["Live Mode (AI Search) - Mode Live (Recherche IA)", "Catalog Mode (Static Demo) - Mode Catalogue (Démo Statique)"])

    # ==========================================
    # ONGLET 1 : PIPELINE LIVE (Temps réel)
    # ==========================================
    with tab_live:
        st.info("""**How it works? - Comment ça marche ?**

Enter a title. The system will search for the song, scan its lyrics, analyze its hidden meaning with an LLM, and build a custom recommendation engine in real time.

Entrez un titre. Le système va chercher la chanson, scanner ses paroles, analyser son sens caché avec un LLM, et construire un moteur de recommandation sur mesure en temps réel.""")
        
        with st.form("live_search"):
            col_search, col_limit = st.columns([4, 1])
            query = col_search.text_input("Which song moves you right now? - Quelle chanson vous touche en ce moment ?", placeholder="Ex: Bohemian Rhapsody - Queen")
            limit = col_limit.number_input("Sample Size - Taille de l'échantillon", min_value=5, max_value=25, value=10, help="Number of similar songs to analyze (warning, larger means slower!) - Nombre de chansons similaires à analyser (attention, plus c'est grand, plus c'est lent !)")
            submit = st.form_submit_button("Start Emotional Analysis - Lancer l'analyse émotionnelle", type="primary")

        if submit and query:
            # Zone de logs pour suivre l'avancement
            status_box = st.status("Starting analysis engine... - Démarrage du moteur d'analyse...", expanded=True)
            
            # Instanciation du pipeline avec callback pour les logs
            pipeline = MusicPipeline(status_callback=status_box.write)
            
            # Exécution
            try:
                tracks, distances, indices = pipeline.run(query, limit)
                status_box.update(label="Analysis completed successfully! - Analyse terminée avec succès !", state="complete", expanded=False)
                
                if tracks and indices is not None:
                    display_live_results(tracks, distances, indices)
                else:
                    st.error("The pipeline could not find sufficient emotional matches. - Le pipeline n'a pas pu trouver de correspondances émotionnelles suffisantes.")
                    st.caption("Try with a more famous song or check your connection. - Essayez avec une chanson plus connue ou vérifiez votre connexion.")
                    
            except Exception as e:
                status_box.update(label="Erreur technique", state="error")
                st.error(f"Une erreur inattendue est survenue : {str(e)}")

    # ==========================================
    # ONGLET 2 : CATALOGUE STATIQUE (JSON)
    # ==========================================
    with tab_static:
        st.markdown("### Pre-analyzed Database - Base de données pré-analysée")
        st.caption("This mode allows you to instantly explore songs already processed by our AI. - Ce mode permet d'explorer instantanément des chansons déjà traitées par notre IA.")
        
        candidates = load_static_data()
        index = load_static_index()

        if not candidates or not index:
            st.warning("No static data found. Use **Live Mode** to start analyzing music! - Aucune donnée statique trouvée. Utilisez le **Mode Live** pour commencer à analyser des musiques !")
        else:
            # Filtrage des chansons valides (avec embeddings)
            valid_songs = [s for s in candidates if s.get("embedding")]
            titles = [f"{s['title']} - {s['artist']}" for s in valid_songs]
            
            col_sel, col_btn = st.columns([3, 1])
            selected = col_sel.selectbox("Choose a song from the catalog: - Choisir une chanson dans le catalogue :", titles)
            
            if col_btn.button("Find similar vibes - Trouver les vibes similaires"):
                # Logique de recherche locale
                idx = titles.index(selected)
                seed_vector = np.array([valid_songs[idx]["embedding"]]).astype("float32")
                
                # Normalisation & Recherche
                faiss.normalize_L2(seed_vector)
                # On cherche k+1 car la chanson elle-même sera le résultat #1 (distance 1.0)
                D, I = index.search(seed_vector, k=min(4, len(valid_songs)))
                
                # Affichage des résultats
                st.subheader(f"If you like '{selected}', our AI suggests: - Si vous aimez '{selected}', notre IA suggère :")
                
                # On ignore le premier résultat (soi-même)
                cols = st.columns(3)
                found_count = 0
                
                for i in range(1, len(I[0])): 
                    match_idx = I[0][i]
                    match_score = D[0][i]
                    
                    if match_idx < len(valid_songs):
                        song = valid_songs[match_idx]
                        with cols[found_count % 3]:
                            render_song_card(song, match_score, i)
                        found_count += 1

def display_live_results(tracks, distances, indices):
    """Affiche les résultats du mode Live de manière structurée"""
    
    # La seed est le premier élément retourné (le plus proche de lui-même)
    seed_idx_in_tracks = indices[0][0]
    seed_track = tracks[seed_idx_in_tracks]
    
    # 1. Affichage de la "Graine" (La chanson source)
    st.markdown("---")
    st.markdown(f"### Analysis of your choice: - Analyse de votre choix : *{seed_track['title']}*")
    
    col_seed_meta, col_seed_analysis = st.columns([1, 2])
    
    with col_seed_meta:
        st.metric("Artist - Artiste", seed_track['artist'])
        if seed_track.get('analysis'):
            emo = seed_track['analysis'].get('emotional_profile', {})
            st.progress(emo.get('valence', 0.5), text="Positivity (Valence) - Positivité (Valence)")
            st.progress(emo.get('arousal', 0.5), text="Energy (Arousal) - Énergie (Arousal)")
            
    with col_seed_analysis:
        if seed_track.get('analysis'):
            ana = seed_track['analysis']
            st.markdown(f"<div class='metric-card'><b>AI detected this Vibe: - L'IA a détecté cette Vibe :</b><br><i>{ana['semantic_layer']['narrative_arc']}</i></div>", unsafe_allow_html=True)
            st.caption(f"Key themes: - Thèmes clés : {', '.join(ana['semantic_layer']['keywords'][:5])}")
        else:
            st.warning("Semantic analysis not available for this track (Instrumental?) - Analyse sémantique non disponible pour ce titre (Instrumental ?)")

    # 2. Affichage des Recommandations
    st.markdown("---")
    st.subheader("Recommendations based on emotional resonance - Recommandations basées sur la résonance émotionnelle")
    
    cols = st.columns(3)
    count = 0
    
    # On itère à partir de 1 pour sauter la seed elle-même
    for i in range(1, len(indices[0])):
        idx_in_tracks = indices[0][i]
        score = distances[0][i]
        
        if idx_in_tracks < len(tracks):
            song = tracks[idx_in_tracks]
            with cols[count % 3]:
                render_song_card(song, score, count + 1)
            count += 1

def render_song_card(song, score, rank):
    """Composant visuel pour afficher une carte de chanson"""
    with st.container():
        st.markdown(f"#### #{rank} {song['title']}")
        st.caption(f"**{song['artist']}**")
        
        if 'youtube_rank' in song:
            st.caption(f"Original YouTube Rank: #{song['youtube_rank']}")
        
        # Jauge de compatibilité colorée
        match_percentage = int(score * 100)
        color = "green" if match_percentage > 70 else "orange" if match_percentage > 50 else "red"
        st.markdown(f"Vibe Compatibility: - Compatibilité de Vibe : **:{color}[{match_percentage}%]**")
        st.progress(float(score))
        
        if song.get("analysis"):
            with st.expander("Why this match? - Pourquoi ce match ?"):
                ana = song["analysis"]
                
                # Récupération sécurisée des données
                traj = ana.get('emotional_profile', {}).get('emotional_trajectory', 'Trajectoire inconnue')
                theme = ana.get('semantic_layer', {}).get('primary_theme', 'Thème inconnu')
                
                st.markdown(f"**Trajectory: - Trajectoire :** {traj}")
                st.markdown(f"**Common Theme: - Thème commun :** {theme}")
                
                if 'vibe_text' in song:
                    st.caption("Semantic Signature (excerpt): - Signature sémantique (extrait) :")
                    st.code(song['vibe_text'][:150] + "...", language="text")
        else:
            st.info("No detailed analysis available. - Pas d'analyse détaillée disponible.")

if __name__ == "__main__":
    main()