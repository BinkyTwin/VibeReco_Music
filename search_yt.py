import ytmusicapi

ytmusic = ytmusicapi.YTMusic()

search_result = ytmusic.search("Tettru", "songs")

if len(search_result) > 0:
    first_track = search_result[0]
    track_id = first_track['videoId']
    track_title = first_track['title']
    track_artist = first_track['artists'][0]['name']

radio = ytmusic.get_watch_playlist(track_id, limit=15)

for i in radio["tracks"]:
    print(i["title"])
    print(i["artists"][0]["name"])
    print("\n")
    print("---------------------------------------")