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
def lookup(name: str, style: str = ""):
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
