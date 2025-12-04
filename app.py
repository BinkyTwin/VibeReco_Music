import streamlit as st
import json
import numpy as np
import faiss
import os

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Deep Vibe Recommender",
    page_icon="🎵",
    layout="wide"
)       

# --- CHARGEMENT DES DONNÉES (CACHÉ) ---

@st.cache_data
def load_candidates():
    """Charge le fichier JSON contenant les métadonnées et les embeddings."""
    # Assure-toi que le chemin est bon par rapport à ton dossier
    path = "docs/candidates_with_embedding.json" 
    if not os.path.exists(path):
        st.error(f"❌ Fichier introuvable : {path}. As-tu lancé l'étape 5 ?")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_resource
def load_index():
    """Charge l'index FAISS en mémoire (optimisé)."""
    path = "docs/my_music_index.faiss"
    if not os.path.exists(path):
        st.error(f"❌ Index introuvable : {path}. As-tu lancé l'étape 7 ?")
        return None
    return faiss.read_index(path)

# --- LOGIQUE DE RECHERCHE ---

def get_recommendations(song_index, index, vectors, k=5):
    """Lance la recherche FAISS pour une chanson donnée."""
    # On récupère le vecteur de la chanson choisie
    query_vector = np.array([vectors[song_index]]).astype("float32")
    
    # Normalisation (Important pour la Cosine Similarity !)
    faiss.normalize_L2(query_vector)
    
    # Recherche (on demande k+1 car la chanson se trouve elle-même en premier)
    distances, indices = index.search(query_vector, k+1)
    
    return distances[0], indices[0]

# --- INTERFACE UTILISATEUR ---

def main():
    # Titre et Intro
    st.title("🎵 Deep Vibe Recommender")
    st.markdown("Explorez la musique par **sens** et **émotion**, pas juste par genre.")
    st.markdown("---")

    # 1. Chargement
    candidates = load_candidates()
    index = load_index()

    if not candidates or not index:
        st.stop() # On arrête tout si les fichiers manquent

    # Préparation des listes pour le menu déroulant
    # On filtre ceux qui ont un embedding valide
    valid_songs = [s for s in candidates if s.get("embedding")]
    song_titles = [f"{s['title']} - {s['artist']}" for s in valid_songs]
    
    # Extraction de tous les vecteurs pour les avoir prêts si besoin (mais FAISS gère déjà)
    # On a juste besoin de l'embedding de la chanson SOURCE pour la requête
    
    # 2. Sidebar : Sélection
    with st.sidebar:
        st.header("🎧 Ma Platine")
        selected_song_name = st.selectbox("Quelle chanson écoutes-tu ?", song_titles)
        
        # Retrouver l'index de la chanson sélectionnée dans notre liste 'valid_songs'
        selected_index = song_titles.index(selected_song_name)
        selected_song_data = valid_songs[selected_index]
        
        st.image("https://cdn-icons-png.flaticon.com/512/4430/4430494.png", width=100)
        st.write(f"**Sélection :** {selected_song_data['title']}")
        
        if st.button("Lancer la recommandation 🚀", type="primary"):
            st.session_state.searched = True

    # 3. Affichage Principal
    if 'searched' in st.session_state and st.session_state.searched:
        
        # A. Affichage de la chanson "Graine" (Seed)
        col1, col2 = st.columns([1, 2])
        with col1:
            st.info("💿 **Chanson de référence**")
            st.header(selected_song_data['title'])
            st.caption(selected_song_data['artist'])
            
            # Affichage des jauges émotionnelles (si l'analyse existe)
            if "analysis" in selected_song_data:
                analysis = selected_song_data["analysis"]
                emo = analysis["emotional_profile"]
                st.progress(emo.get("valence", 0.5), text="Valence (Joie/Tristesse)")
                st.progress(emo.get("arousal", 0.5), text="Arousal (Énergie)")
        
        with col2:
            if "analysis" in selected_song_data:
                st.markdown(f"**📝 L'analyse de l'IA :**")
                st.write(f"_{selected_song_data['analysis']['semantic_layer']['narrative_arc']}_")
                st.markdown(f"**Thèmes :** {', '.join(selected_song_data['analysis']['semantic_layer']['keywords'][:5])}")

        st.markdown("---")
        st.subheader("✨ Recommandations Similaires")

        # B. Calcul des voisins
        # On reconstruit la matrice de vecteurs pour FAISS (si nécessaire) ou on pioche
        # Pour simplifier ici, on suppose que l'ordre de valid_songs correspond à l'ordre d'indexation FAISS de l'étape 7
        # ATTENTION : Cela suppose que tu as indexé 'valid_songs' dans le même ordre à l'étape 7.
        
        all_vectors = np.array([s['embedding'] for s in valid_songs]).astype("float32")
        scores, indices = get_recommendations(selected_index, index, all_vectors)

        # C. Affichage des résultats (Grille)
        cols = st.columns(3) # 3 colonnes
        
        # On ignore le premier résultat (c'est la chanson elle-même)
        for i in range(1, 4): # On affiche le Top 3
            idx_match = indices[i]
            score_match = scores[i]
            song_match = valid_songs[idx_match]
            
            with cols[i-1]:
                st.markdown(f"### {i}. {song_match['title']}")
                st.caption(song_match['artist'])
                
                # Score de similarité
                st.metric(label="Compatibilité", value=f"{int(score_match * 100)}%")
                
                # Détails dans un menu déroulant
                with st.expander("Pourquoi cette recommandation ?"):
                    if "analysis" in song_match:
                        match_data = song_match["analysis"]
                        st.write(f"**Ambiance :** {match_data['emotional_profile']['emotional_trajectory']}")
                        st.write(f"**Thèmes communs :** {match_data['semantic_layer']['primary_theme']}")
                    else:
                        st.write("Pas d'analyse détaillée disponible.")

if __name__ == "__main__":
    main()
