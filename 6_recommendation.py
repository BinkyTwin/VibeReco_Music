import json
import numpy as np
import faiss
import os

# 1. Chargement des données
print("Chargement des embeddings...")
with open("docs/candidates_with_embedding.json", "r", encoding="utf-8") as f:
    candidates = json.load(f)

titres = []
vectors = []
mapping_titre_index = {} # Pour retrouver l'ID d'une chanson grâce à son titre

# On filtre et on remplit nos listes
for i, song in enumerate(candidates):
    if song.get("embedding"):
        idx_dans_faiss = len(titres) # L'index actuel dans nos listes propres
        titres.append(song["title"])
        vectors.append(song["embedding"])
        mapping_titre_index[song["title"].lower()] = idx_dans_faiss

# 2. Préparation FAISS
print("Construction de l'Index FAISS...")
vectors = np.array(vectors).astype("float32")
faiss.normalize_L2(vectors)
index = faiss.IndexFlatIP(vectors.shape[1])
index.add(vectors)

faiss.write_index(index, "docs/my_music_index.faiss")
print(f"Index sauvegardé avec {index.ntotal} vecteurs.")

def recommend(song_title, k=5):
    """
    Trouve les k chansons les plus proches du titre donné.
    """
    # A. On trouve l'ID de la chanson
    song_id = mapping_titre_index.get(song_title.lower())
    
    if song_id is None:
        return f"Chanson '{song_title}' introuvable dans la base."

    # B. On récupère son vecteur
    query_vector = np.array([vectors[song_id]]).astype("float32")
    faiss.normalize_L2(query_vector)

    # C. On lance la recherche
    distances, indices = index.search(query_vector, k+1)

    print(f"\n Recommandations pour '{song_title}' :")
    print("-" * 30)
    
    # D. Affichage propre
    # On saute le premier résultat (0) car c'est la chanson elle-même
    found_count = 0
    for i in range(1, len(indices[0])):
        idx_voisin = indices[0][i]
        score = distances[0][i]
        
        # Petite sécurité si l'index est hors limites (rare)
        if idx_voisin < len(titres):
            print(f"{found_count + 1}. {titres[idx_voisin]} (Similarité : {score:.4f})")
            found_count += 1

# --- TEST ---
# Essaie avec différents titres de ta liste !
recommend("Stand By Me")
recommend("Be My Baby")