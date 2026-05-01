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

def wiki_lookup(name: str):
    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + name.replace(" ", "_")
    r = requests.get(url)

    if r.status_code != 200:
        return None

    data = r.json()

    return {
        "title": data.get("title"),
        "desc": data.get("extract"),
        "image": data.get("thumbnail", {}).get("source", "")
    }

@app.get("/lookup")
def lookup(name: str):
    data = wiki_lookup(name)

    if not data:
        return {
            "found": False,
            "prompt": f"highly detailed original character inspired by {name}",
            "image": ""
        }

    return {
        "found": True,
        "prompt": f"{data['title']}, {data['desc']}, highly detailed anime style character portrait",
        "image": data["image"]
    }
