from sklearn.metrics.pairwise import cosine_similarity
import json
import numpy as np

with open("docs/candidates_with_embedding.json", "r") as f:
    vector_json = json.load(f)

titres = []
vector = []
for song in vector_json:
    try: 
        titres.append(song["title"])
        vector.append(song["embedding"])
    except Exception as e:
        print(f"Error for {song['title']} by {song['artist']}: {str(e)}")