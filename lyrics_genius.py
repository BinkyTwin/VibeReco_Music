import os
from lyricsgenius import Genius
from dotenv import load_dotenv
import json
import time

load_dotenv()

token_genius = os.getenv('TOKEN_GENIUS')

genius = Genius(token_genius, remove_section_headers=True, verbose=False)

#Importation du fichier candidate_list.json
with open("docs/candidate_list.json", "r") as f:
    candidate_list = json.load(f)

for candidate in candidate_list:
    title = candidate["title"]
    artist = candidate["artist"]

    try:
        song = genius.search_song(title, artist)
        if song:
            candidate["lyrics"] = song.lyrics
            candidate["status"] = "found"
            print(f"Lyrics saved for {title} by {artist}")
        else:
            candidate["lyrics"] = None
            candidate["status"] = "not found"
            print(f"Lyrics not found for {title} by {artist}")
    except Exception as e:
        candidate["lyrics"] = None
        candidate["status"] = "error"
        print(f"Error for {title} by {artist}: {str(e)}")

    #Pause de 1 seconde entre chaque requête pour éviter de surcharger l'API
    time.sleep(1)

#Sauvegarde de la liste des chansons dans un fichier
with open("docs/candidate_list_with_lyrics.json", "w") as f:
    json.dump(candidate_list, f, indent=4, ensure_ascii=False)
    print("Lyrics saved for all songs")