from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HEADERS = {
    "User-Agent": "character-lookup/1.0 (https://github.com/Tannergit7051/character-lookup)"
}

def jikan_lookup(name: str):
    url = "https://api.jikan.moe/v4/characters?q=" + name + "&limit=5"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        return None
    data = r.json()
    results = data.get("data", [])
    if not results:
        return None
    name_lower = name.lower().split()[0]
    best = None
    for char in results:
        char_name = char.get("name", "").lower()
        if name_lower in char_name:
            best = char
            break
    if not best:
        best = results[0]
    about = best.get("about", "") or ""
    about = about[:300]
    image = best.get("images", {}).get("jpg", {}).get("image_url", "")
    return {
        "title": best.get("name", name),
        "desc": about,
        "image": image
    }

def wiki_lookup(name: str):
    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + name.replace(" ", "_")
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        return None
    data = r.json()
    if data.get("type") == "disambiguation":
        return None
    return {
        "title": data.get("title"),
        "desc": data.get("extract"),
        "image": data.get("thumbnail", {}).get("source", "")
    }

@app.get("/lookup")
def lookup(name: str):
    data = jikan_lookup(name)
    if not data:
        data = wiki_lookup(name)
    if not data:
        return {
            "found": False,
            "prompt": name + ", original character, highly detailed, expressive face, dynamic pose, intricate costume design, vibrant colors",
            "image": ""
        }
    return {
        "found": True,
        "prompt": data['title'] + ", " + data['desc'] + ", highly detailed anime style character portrait",
        "image": data["image"]
    }
