import ytmusicapi
from lyricsgenius import Genius
from src.config import TOKEN_GENIUS
import time
import re

def get_youtube_recommendations(seed_query, limit=10):
    """
    Retrieves song recommendations from YouTube Music based on a seed query.
    
    Searches for a song on YouTube Music and generates a radio playlist of similar tracks.
    Returns a list of recommended songs with their metadata.
    
    Args:
        seed_query: Search query string (song title, artist, or combination)
        limit: Maximum number of recommendations to return (default: 10)
        
    Returns:
        list: List of dictionaries containing track information:
            - title: Song title
            - artist: Artist name
            - videoId: YouTube video ID
        None: If the search returns an artist instead of a song, or no results found
    """
    yt = ytmusicapi.YTMusic()
    search_results = yt.search(seed_query, limit=limit)

    tracks = []

    if len(search_results) > 0:
        if search_results[0]['resultType'] == 'artist':
            print("Artist found, please search a song")
            return None
        else:
            first_track = search_results[0]
            track_id = first_track.get('videoId')
            
            # Vérifier que le videoId existe et n'est pas None
            if not track_id:
                print(f"Aucun videoId trouvé pour: {seed_query}")
                return None
            
            radio = yt.get_watch_playlist(track_id, limit=10)

            for track in radio["tracks"][:limit]:
                chanson_propre = {
                    "title": track["title"],
                    "artist": track["artists"][0]["name"],
                    "videoId": track["videoId"]
                }
                tracks.append(chanson_propre)
    else:
        print("Aucune chanson trouvée pour la requête :", seed_query)
    
    return tracks

def fetch_lyrics(tracks):
    """
    Fetches lyrics for a list of tracks using the Genius API.
    
    Iterates through the provided tracks and attempts to retrieve lyrics from Genius.
    Updates each track dictionary with lyrics and status information. Includes a 1-second
    delay between requests to respect API rate limits.
    
    Args:
        tracks: List of track dictionaries containing 'title' and 'artist' keys
        
    Returns:
        list: Updated list of tracks with added fields:
            - lyrics: Song lyrics text (or None if not found)
            - status: "found" or "not found"
        None: If tracks parameter is None (artist search result)
        
    Side effects:
        Prints status messages for each track processed
    """
    if tracks is None:
        print("Artist found, please search a song")
        return None
    else:
        yt = ytmusicapi.YTMusic()
        genius = Genius(TOKEN_GENIUS, verbose=False, remove_section_headers=True)
        
        for candidate in tracks:
            lyrics_found = False
            
            # 1. Try YTMusic (Fast)
            try:
                print(f"Attempting YTMusic for: {candidate['title']}")
                watch_data = yt.get_watch_playlist(candidate["videoId"])
                if "lyrics" in watch_data and watch_data["lyrics"]:
                    lyrics_data = yt.get_lyrics(watch_data["lyrics"])
                    if lyrics_data and "lyrics" in lyrics_data:
                        candidate["lyrics"] = lyrics_data["lyrics"]
                        candidate["status"] = "found"
                        candidate["source"] = "ytmusic"
                        print(f"  -> Found lyrics via YTMusic")
                        lyrics_found = True
            except Exception as e:
                print(f"  -> YTMusic error: {e}")

            # 2. Fallback to Genius (Reliable)
            if not lyrics_found:
                try: 
                    print(f"Fallback to Genius for: {candidate['title']}")
                    # Clean title to remove noise like "(Official Audio)"
                    clean_title = re.sub(r"[\(\[].*?(official|video|audio|lyrics|version|remaster|remaster version).*?[\)\]]", "", candidate["title"], flags=re.IGNORECASE).strip()
                    
                    song = genius.search_song(clean_title, candidate["artist"])
                    if song:
                        candidate["lyrics"] = song.lyrics
                        candidate["status"] = "found"
                        candidate["source"] = "genius"
                        print(f"  -> Found lyrics via Genius (searched as '{clean_title}')")
                    else:
                        candidate["lyrics"] = None
                        candidate["status"] = "not found"
                        print(f"  -> Lyrics not found on Genius")
                except Exception as e:
                    candidate["lyrics"] = None
                    candidate["status"] = "not found"
                    print(f"  -> Genius error: {str(e)}")
        
        time.sleep(1)
    
        return tracks


