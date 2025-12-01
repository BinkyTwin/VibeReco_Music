import os
import ytmusicapi
from lyricsgenius import Genius
from dotenv import load_dotenv
import json

recommandation_list = []

load_dotenv()

client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
token_genius = os.getenv('TOKEN_GENIUS')

ytmusic = ytmusicapi.YTMusic()

search_result = ytmusic.search("Tettru", "songs")

if len(search_result) > 0:
    first_track = search_result[0]
    track_id = first_track['videoId']
    track_title = first_track['title']
    track_artist = first_track['artists'][0]['name']

radio = ytmusic.get_watch_playlist(track_id, limit=15)

for track in radio["tracks"]:
    chanson_propre = {
        "title": track["title"],
        "artist": track["artists"][0]["name"],
        "videoId": track["videoId"]
    }
    recommandation_list.append(chanson_propre)
    print("YT Recommandation liste récupérer !")

with open("docs/candidate_list.json", "w") as f:
    json.dump(recommandation_list, f, indent=4, ensure_ascii=False)
