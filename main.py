from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import time
import re

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

cache = {}
CACHE_DURATION = 3600

def extract_visual_details(text, char_name):
    """Extract visual characteristics from character description"""
    if not text:
        return ""
    
    # Common visual keywords to look for
    visual_keywords = [
        'hair', 'eyes', 'skin', 'tall', 'short', 'wears', 'outfit', 'clothing',
        'appearance', 'looks', 'face', 'build', 'muscular', 'slim', 'height',
        'blonde', 'black', 'brown', 'blue', 'green', 'red', 'white', 'gray',
        'scar', 'tattoo', 'mark', 'distinctive', 'features', 'costume', 'uniform',
        'glasses', 'hat', 'armor', 'sword', 'weapon', 'carries', 'signature'
    ]
    
    sentences = re.split(r'[.!?]+', text)
    visual_sentences = []
    
    for sentence in sentences:
        sentence_lower = sentence.lower()
        if any(keyword in sentence_lower for keyword in visual_keywords):
            visual_sentences.append(sentence.strip())
            if len(visual_sentences) >= 3:  # Get up to 3 visual sentences
                break
    
    if visual_sentences:
        return char_name + ", " + " ".join(visual_sentences)
    else:
        # Fallback to first 100 words if no visual keywords found
        words = text.split()[:100]
        return char_name + ", " + " ".join(words)

def jikan_lookup(name: str):
    cache_key = "jikan_" + name.lower()
    if cache_key in cache:
        cached_time, cached_data = cache[cache_key]
        if time.time() - cached_time < CACHE_DURATION:
            return cached_data
    
    url = "https://api.jikan.moe/v4/characters?q=" + name + "&limit=8"
    try:
        r = requests.get(url, headers=HEADERS, timeout=5)
        if r.status_code != 200:
            return None
        data = r.json()
        results = data.get("data", [])
        if not results:
            return None
        
        name_lower = name.lower()
        best = None
        for char in results:
            char_name = char.get("name", "").lower()
            if name_lower == char_name or name_lower in char_name.split():
                best = char
                break
        
        if not best:
            best = results[0]
        
        char_name = best.get("name", name)
        about = best.get("about", "") or ""
        
        # Extract visual details
        visual_desc = extract_visual_details(about, char_name)
        
        image = best.get("images", {}).get("jpg", {}).get("image_url", "")
        
        result = {
            "title": char_name,
            "desc": visual_desc,
            "image": image,
            "source": "jikan"
        }
        cache[cache_key] = (time.time(), result)
        return result
    except Exception as e:
        return None

def wiki_lookup(name: str):
    cache_key = "wiki_" + name.lower()
    if cache_key in cache:
        cached_time, cached_data = cache[cache_key]
        if time.time() - cached_time < CACHE_DURATION:
            return cached_data
    
    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + name.replace(" ", "_")
    try:
        r = requests.get(url, headers=HEADERS, timeout=5)
        if r.status_code != 200:
            return None
        data = r.json()
        if data.get("type") == "disambiguation":
            return None
        
        title = data.get("title", name)
        extract = data.get("extract", "")
        
        # For Wikipedia, use the full extract since it's already concise
        visual_desc = extract_visual_details(extract, title) if extract else title
        
        result = {
            "title": title,
            "desc": visual_desc,
            "image": data.get("thumbnail", {}).get("source", ""),
            "source": "wikipedia"
        }
        cache[cache_key] = (time.time(), result)
        return result
    except Exception as e:
        return None

# Manual character database for common characters that APIs get wrong
MANUAL_CHARS = {
    "nami": {
        "title": "Nami",
        "desc": "Nami, orange hair, brown eyes, slim build, often wears revealing outfits, carries a Clima-Tact staff, navigator from One Piece, has a tattoo on her left shoulder",
        "image": "",
        "source": "manual"
    },
    "luffy": {
        "title": "Monkey D. Luffy",
        "desc": "Monkey D. Luffy, black hair, wears a straw hat, red vest, blue shorts, scar under left eye, always smiling, rubber powers, One Piece protagonist",
        "image": "",
        "source": "manual"
    },
    "zoro": {
        "title": "Roronoa Zoro",
        "desc": "Roronoa Zoro, green hair, three earrings on left ear, muscular build, carries three swords, scar over left eye, wears open shirt, serious expression, One Piece swordsman",
        "image": "",
        "source": "manual"
    },
    "naruto": {
        "title": "Naruto Uzumaki",
        "desc": "Naruto Uzumaki, spiky blonde hair, blue eyes, whisker marks on face, orange and black jumpsuit, headband with leaf symbol, energetic expression, ninja from Naruto series",
        "image": "",
        "source": "manual"
    },
    "goku": {
        "title": "Son Goku",
        "desc": "Son Goku, spiky black hair, orange gi with blue undershirt, martial arts belt, muscular build, confident smile, Saiyan from Dragon Ball, may have Super Saiyan golden hair",
        "image": "",
        "source": "manual"
    }
}

@app.get("/lookup")
def lookup(name: str):
    # Check manual database first
    name_clean = name.lower().strip()
    if name_clean in MANUAL_CHARS:
        return {
            "found": True,
            "prompt": MANUAL_CHARS[name_clean]["desc"] + ", highly detailed anime character portrait",
            "image": MANUAL_CHARS[name_clean]["image"],
            "source": MANUAL_CHARS[name_clean]["source"]
        }
    
    # Try API sources
    data = jikan_lookup(name)
    if not data:
        data = wiki_lookup(name)
    
    if not data:
        return {
            "found": False,
            "prompt": name + ", original character, expressive face, dynamic pose, intricate costume design, detailed hair and eyes, vibrant colors, full body portrait",
            "image": "",
            "source": "fallback"
        }
    
    return {
        "found": True,
        "prompt": data['desc'] + ", highly detailed character portrait, anime style",
        "image": data["image"],
        "source": data.get("source", "unknown")
    }

@app.get("/")
def root():
    return {
        "status": "Character Lookup API Running",
        "endpoints": ["/lookup?name=CHARACTER_NAME"],
        "manual_characters": list(MANUAL_CHARS.keys())
    }
