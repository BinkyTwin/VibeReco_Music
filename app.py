import streamlit as st
import numpy as np
import os
import json
import faiss
from src.pipeline import MusicPipeline

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Deep Vibe Recommender",
    page_icon="🎵",
    layout="wide"
)

# --- FONCTIONS UTILITAIRES POUR LE MODE CATALOGUE (STATIC) ---
@st.cache_data
def load_static_data():
    path = "docs/candidates_with_embedding.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

@st.cache_resource
def load_static_index():
    path = "docs/my_music_index.faiss"
    if os.path.exists(path):
        return faiss.read_index(path)
    return None

# --- UI PRINCIPALE ---
def main():
    st.title("🎹 Deep Vibe Recommender")
    st.markdown("Recommandation musicale par **sens**, **émotion** et **vibe**.")

    tab_live, tab_static = st.tabs(["⚡ Mode Live (Pipeline)", "📂 Mode Catalogue (Statique)"])

    # ==========================================
    # ONGLET 1 : PIPELINE LIVE (Temps réel)
    # ==========================================
    with tab_live:
        st.caption("Lance le processus complet : YouTube -> Genius -> LLM -> FAISS")
        
        with st.form("live_search"):
            col1, col2 = st.columns([3, 1])
            query = col1.text_input("Titre ou Artiste", placeholder="Ex: Bohemian Rhapsody...")
            limit = col2.number_input("Nombre de candidats", min_value=4, max_value=20, value=8)
            submit = st.form_submit_button("Lancer l'analyse")

        if submit and query:
            # Zone de logs pour suivre l'avancement
            status_box = st.status("Démarrage du pipeline...", expanded=True)
            
            # Instanciation du pipeline avec une fonction de log qui écrit dans le status_box
            pipeline = MusicPipeline(status_callback=status_box.write)
            
            # Exécution
            try:
                result = pipeline.run(query, limit, return_youtube_tracks=True)
                
                # Check if we got YouTube tracks
                if result and result.get("youtube_tracks"):
                    youtube_tracks = result["youtube_tracks"]
                    
                    # Display YouTube Radio results
                    status_box.update(label="YouTube Music - Radio générée", state="running", expanded=True)
                    
                    with st.expander("🎵 Musiques trouvées dans la radio YouTube Music", expanded=True):
                        st.caption(f"**Chanson seed:** {youtube_tracks[0]['title']} - {youtube_tracks[0]['artist']}\nVoici les {limit} chansons recommandées par YouTube Music avant l'analyse LLM, alors est-ce que c'est différent du résultat obtenu par le LLM ?")
                        st.divider()
                        
                        # Display all tracks in a nice grid
                        cols = st.columns(3)
                        for idx, track in enumerate(youtube_tracks):
                            with cols[idx % 3]:
                                if idx == 0:
                                    st.markdown(f"**{track['title']}**")
                                    st.caption(f"{track['artist']}")
                                    st.success("Chanson de référence")
                                else:
                                    st.markdown(f"**#{idx} {track['title']}**")
                                    st.caption(f"{track['artist']}")
                    
                    # Display lyrics status after they are fetched
                    if result.get("tracks_with_lyrics"):
                        tracks_with_lyrics = result["tracks_with_lyrics"]
                        
                        with st.expander("📝 Statut des paroles récupérées", expanded=False):
                            cols = st.columns(3)
                            for idx, track in enumerate(tracks_with_lyrics):
                                with cols[idx % 3]:
                                    st.markdown(f"**{track['title']}**")
                                    st.caption(f"{track['artist']}")
                                    
                                    if track.get("status") == "found":
                                        st.success("✓ Paroles trouvées")
                                    else:
                                        st.error("✗ Paroles non trouvées")
                    
                    status_box.update(label="Analyse en cours...", state="running", expanded=True)
                
                # Wait for final results
                status_box.update(label="Terminé !", state="complete", expanded=False)
                
                tracks = result.get("final_tracks")
                distances = result.get("distances")
                indices = result.get("indices")
                
                if tracks and indices is not None:
                    display_results(tracks, distances, indices)
                else:
                    st.error("Le pipeline n'a pas retourné de résultats exploitables.")
                    
            except Exception as e:
                status_box.update(label="Erreur", state="error")
                st.error(f"Une erreur est survenue : {str(e)}")

    # ==========================================
    # ONGLET 2 : CATALOGUE STATIQUE (JSON)
    # ==========================================
    with tab_static:
        st.caption("Explore la base de données déjà analysée.")
        candidates = load_static_data()
        index = load_static_index()

        if not candidates or not index:
            st.warning("Aucune donnée statique trouvée dans 'docs/'. Utilisez le Mode Live ou lancez les scripts d'extraction.")
        else:
            valid_songs = [s for s in candidates if s.get("embedding")]
            titles = [f"{s['title']} - {s['artist']}" for s in valid_songs]
            
            selected = st.selectbox("Choisir une chanson dans la base :", titles)
            
            if st.button("Chercher les vibes similaires"):
                # Retrouver l'index
                idx = titles.index(selected)
                seed_vector = np.array([valid_songs[idx]["embedding"]]).astype("float32")
                
                # Normalisation & Recherche (Logique locale simple ici)
                faiss.normalize_L2(seed_vector)
                D, I = index.search(seed_vector, k=6)
                
                # Affichage
                # On triche un peu en reconstruisant une liste 'tracks' triée pour la fonction d'affichage
                # Mais pour simplifier, on affiche juste ici
                st.subheader(f"Similaires à : {selected}")
                cols = st.columns(3)
                for i in range(1, len(I[0])): # On saute le premier (soi-même)
                    match_idx = I[0][i]
                    match_score = D[0][i]
                    if match_idx < len(valid_songs):
                        song = valid_songs[match_idx]
                        with cols[(i-1)%3]:
                            render_song_card(song, match_score, i)

def display_results(tracks, distances, indices):
    """Fonction d'affichage des résultats pour le mode Live"""
    st.divider()
    
    # La seed est toujours le premier élément retourné par FAISS (distance la plus élevée/proche)
    # Dans notre pipeline, tracks contient les objets, indices contient les positions dans 'tracks'
    
    # Indice 0 de la recherche = La chanson elle-même (Seed)
    seed_idx_in_tracks = indices[0][0] 
    seed_track = tracks[seed_idx_in_tracks]
    
    st.subheader(f"Résultats pour : {seed_track['title']} - {seed_track['artist']}")
    
    # Affichage des recommandations (on commence à 1 pour ignorer la seed)
    cols = st.columns(3)
    count = 0
    
    for i in range(1, len(indices[0])):
        idx_in_tracks = indices[0][i]
        score = distances[0][i]
        
        # Sécurité
        if idx_in_tracks < len(tracks):
            song = tracks[idx_in_tracks]
            with cols[count % 3]:
                render_song_card(song, score, count + 1)
            count += 1

def render_song_card(song, score, rank):
    """Affiche une jolie carte pour une chanson"""
    st.markdown(f"#### #{rank} {song['title']}")
    st.caption(f"Artiste : {song['artist']}")
    st.progress(float(score), text=f"Compatibilité : {int(score*100)}%")
    
    if song.get("analysis"):
        with st.expander("Voir l'analyse"):
            ana = song["analysis"]
            st.write(f"**Vibe:** {ana['emotional_profile']['emotional_trajectory']}")
            st.write(f"**Thèmes:** {', '.join(ana['semantic_layer']['keywords'][:3])}")
    else:
        st.info("Pas d'analyse textuelle (Instrumental ?)")

if __name__ == "__main__":
    main()