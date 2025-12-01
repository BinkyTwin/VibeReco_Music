import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(
    api_key=openai_api_key,
    base_url="https://api.openai.com/v1"
)

with open("docs/candidates_with_vibe_text.json", "r") as f:
    analyse_json = json.load(f)

for song in analyse_json:
    if song.get("vibe_text"):
        try: 
            completion = client.embeddings.create(
                model="text-embedding-3-small",
                input=song["vibe_text"]
            )
            song["embedding"] = completion.data[0].embedding
        except Exception as e:
            song["embedding"] = None
            print(f"Error for {song['title']} by {song['artist']}: {str(e)}")
    else:
        song["embedding"] = None
        print(f"Song without vibe text : {song['title']} - {song['artist']}")

with open("docs/candidates_with_embedding.json", "w") as f:
    json.dump(analyse_json, f, indent=4, ensure_ascii=False)
    print("All songs with embedding saved in candidates_with_embedding.json")


    