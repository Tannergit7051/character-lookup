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

def extract_physical_features(text, char_name):
    """Extract highly detailed physical appearance from text"""
    if not text:
        return char_name + ", detailed character design"
    
    # Physical feature keywords - expanded list
    appearance_keywords = [
        # Hair
        'hair', 'hairstyle', 'haircut', 'bangs', 'ponytail', 'braid', 'spiky', 'curly', 'straight',
        'blonde', 'brunette', 'black-haired', 'white-haired', 'silver', 'gray', 'red-haired',
        # Eyes
        'eyes', 'eye color', 'pupils', 'gaze', 'stare', 'blue eyes', 'green eyes', 'brown eyes',
        'red eyes', 'yellow eyes', 'heterochromia', 'glasses', 'eyepatch',
        # Face
        'face', 'facial', 'cheeks', 'jaw', 'chin', 'nose', 'mouth', 'lips', 'teeth', 'fangs',
        'smile', 'smiling', 'grin', 'expression', 'scar', 'scars', 'tattoo', 'marking', 'birthmark',
        'whiskers', 'beard', 'mustache', 'freckles',
        # Body
        'tall', 'short', 'height', 'build', 'physique', 'muscular', 'slim', 'slender', 'petite',
        'athletic', 'stocky', 'burly', 'lean', 'skinny', 'chubby', 'body', 'figure',
        # Skin
        'skin', 'complexion', 'pale', 'tan', 'dark', 'fair', 'light',
        # Clothing
        'wears', 'wearing', 'dressed', 'outfit', 'clothing', 'costume', 'uniform', 'suit',
        'dress', 'shirt', 'jacket', 'coat', 'pants', 'boots', 'shoes', 'hat', 'cape', 'cloak',
        'armor', 'robe', 'kimono', 'gi', 'vest', 'gloves', 'belt', 'scarf', 'headband',
        'mask', 'helmet', 'crown', 'necklace', 'earrings', 'jewelry',
        # Colors
        'red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink', 'black', 'white',
        'gold', 'golden', 'silver', 'bronze', 'brown', 'gray', 'grey',
        # Accessories & weapons
        'carries', 'holds', 'weapon', 'sword', 'staff', 'gun', 'blade', 'shield', 'bow',
        'wings', 'tail', 'horns', 'ears', 'animal', 'creature',
        # Distinctive features
        'distinctive', 'notable', 'signature', 'iconic', 'recognizable', 'trademark',
        'appearance', 'look', 'design', 'style', 'aesthetic'
    ]
    
    # Split into sentences
    sentences = re.split(r'[.!?]+', text)
    visual_sentences = []
    other_sentences = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        sentence_lower = sentence.lower()
        
        # Count visual keywords in this sentence
        visual_count = sum(1 for keyword in appearance_keywords if keyword in sentence_lower)
        
        if visual_count >= 1:  # At least one visual keyword
            visual_sentences.append(sentence)
        else:
            other_sentences.append(sentence)
    
    # Build description prioritizing physical details
    description_parts = [char_name]
    
    # Add all visual sentences first
    if visual_sentences:
        description_parts.extend(visual_sentences[:6])  # Up to 6 visual sentences
    
    # If we don't have enough detail, add some context sentences
    if len(description_parts) < 4 and other_sentences:
        description_parts.extend(other_sentences[:2])
    
    # Join and clean up
    full_desc = ", ".join(description_parts)
    
    # Remove extra spaces and fix punctuation
    full_desc = re.sub(r'\s+', ' ', full_desc)
    full_desc = re.sub(r'\s*,\s*,\s*', ', ', full_desc)
    
    return full_desc

def jikan_lookup(name: str):
    """Fetch from Jikan (MyAnimeList) API"""
    cache_key = "jikan_" + name.lower()
    if cache_key in cache:
        cached_time, cached_data = cache[cache_key]
        if time.time() - cached_time < CACHE_DURATION:
            return cached_data
    
    url = "https://api.jikan.moe/v4/characters?q=" + name + "&limit=10"
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        if r.status_code != 200:
            return None
        data = r.json()
        results = data.get("data", [])
        if not results:
            return None
        
        # Try to find best match
        name_lower = name.lower()
        best = None
        
        for char in results:
            char_name = char.get("name", "").lower()
            # Exact match
            if name_lower == char_name:
                best = char
                break
            # Name contains search term
            if name_lower in char_name or any(part in char_name for part in name_lower.split()):
                best = char
                break
        
        # Fallback to first result
        if not best:
            best = results[0]
        
        char_name = best.get("name", name)
        about = best.get("about", "") or ""
        
        # Extract physical description
        description = extract_physical_features(about, char_name)
        
        image = best.get("images", {}).get("jpg", {}).get("image_url", "")
        
        result = {
            "title": char_name,
            "desc": description,
            "image": image,
            "source": "jikan"
        }
        
        cache[cache_key] = (time.time(), result)
        return result
        
    except Exception as e:
        print(f"Jikan error: {e}")
        return None

def wiki_lookup(name: str):
    """Fetch from Wikipedia API"""
    cache_key = "wiki_" + name.lower()
    if cache_key in cache:
        cached_time, cached_data = cache[cache_key]
        if time.time() - cached_time < CACHE_DURATION:
            return cached_data
    
    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + name.replace(" ", "_")
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        if r.status_code != 200:
            return None
        data = r.json()
        
        # Skip disambiguation pages
        if data.get("type") == "disambiguation":
            return None
        
        title = data.get("title", name)
        extract = data.get("extract", "")
        
        # Extract physical description
        description = extract_physical_features(extract, title)
        
        result = {
            "title": title,
            "desc": description,
            "image": data.get("thumbnail", {}).get("source", ""),
            "source": "wikipedia"
        }
        
        cache[cache_key] = (time.time(), result)
        return result
        
    except Exception as e:
        print(f"Wikipedia error: {e}")
        return None

# Highly detailed manual character database
MANUAL_CHARS = {
    "nami": {
        "title": "Nami",
        "desc": "Nami, long orange hair, brown eyes, slim athletic build, typically wears revealing bikini tops with low-rise jeans or skirts, has a blue and white striped tattoo on her left shoulder representing her past, carries a long orange and blue Clima-Tact staff, often wears high heels, confident and stylish appearance, navigator of the Straw Hat Pirates from One Piece anime",
        "image": "",
        "source": "manual"
    },
    "luffy": {
        "title": "Monkey D. Luffy",
        "desc": "Monkey D. Luffy, spiky black messy hair, large round black eyes, wide enthusiastic smile showing teeth, scar under left eye, wears iconic straw hat with red ribbon, red sleeveless vest left unbuttoned, blue jean shorts with yellow sash belt, sandals, slim but muscular build, short stature, always has energetic cheerful expression, stretchy rubber body, protagonist of One Piece anime",
        "image": "",
        "source": "manual"
    },
    "zoro": {
        "title": "Roronoa Zoro",
        "desc": "Roronoa Zoro, short spiky green hair, stern dark eyes, scar running over left eye which is usually closed, three gold earrings on left ear, extremely muscular athletic build, tan skin, wears open dark green haramaki around waist, black bandana tied on left arm, carries three katana swords, serious intimidating expression, often shirtless showing battle scars on torso, swordsman of Straw Hat Pirates from One Piece anime",
        "image": "",
        "source": "manual"
    },
    "naruto": {
        "title": "Naruto Uzumaki",
        "desc": "Naruto Uzumaki, spiky blonde hair, bright blue eyes, three whisker-like marks on each cheek, wears orange and black tracksuit jacket, blue sandals, orange pants, blue headband with metal plate bearing Leaf Village symbol worn on forehead, energetic smile, carries kunai knives and scrolls, athletic build, short to medium height, hyperactive cheerful expression, ninja protagonist from Naruto anime series",
        "image": "",
        "source": "manual"
    },
    "sasuke": {
        "title": "Sasuke Uchiha",
        "desc": "Sasuke Uchiha, black spiky hair styled backwards, black eyes that turn red with tomoe pattern when using Sharingan, pale skin, lean muscular build, wears dark blue high-collared shirt, white arm warmers, white shorts, blue sandals, carries katana sword on back, serious brooding expression, cool and aloof appearance, rival character from Naruto anime series",
        "image": "",
        "source": "manual"
    },
    "goku": {
        "title": "Son Goku",
        "desc": "Son Goku, wild spiky black hair that defies gravity, dark eyes, orange gi martial arts uniform with blue undershirt and belt, blue boots and wristbands, muscular athletic build, confident friendly smile, can transform to have golden blonde spiky hair and turquoise eyes in Super Saiyan form, carries Power Pole staff, martial artist protagonist from Dragon Ball anime series",
        "image": "",
        "source": "manual"
    },
    "vegeta": {
        "title": "Vegeta",
        "desc": "Vegeta, black flame-shaped spiky hair, dark eyes, stern prideful expression, wears blue and white Saiyan armor with white gloves and boots, muscular compact build, shorter than Goku, crossed arms pose, widow's peak hairline, can transform to golden blonde spiky hair in Super Saiyan form, Saiyan prince from Dragon Ball anime series",
        "image": "",
        "source": "manual"
    },
    "sakura": {
        "title": "Sakura Haruno",
        "desc": "Sakura Haruno, short pink hair, green eyes, fair skin, red qipao dress with white circular designs, dark shorts underneath, blue sandals, forehead protector headband worn as hairband, medical ninja with enhanced strength, determined expression, slim athletic build, from Naruto anime series",
        "image": "",
        "source": "manual"
    }
}

@app.get("/lookup")
def lookup(name: str):
    """Main lookup endpoint"""
    # Check manual database first (highest quality)
    name_clean = name.lower().strip()
    
    # Try exact match
    if name_clean in MANUAL_CHARS:
        return {
            "found": True,
            "prompt": MANUAL_CHARS[name_clean]["desc"] + ", highly detailed anime character portrait, professional illustration",
            "image": MANUAL_CHARS[name_clean]["image"],
            "source": MANUAL_CHARS[name_clean]["source"]
        }
    
    # Try partial match in manual database
    for key, char_data in MANUAL_CHARS.items():
        if name_clean in key or key in name_clean:
            return {
                "found": True,
                "prompt": char_data["desc"] + ", highly detailed anime character portrait, professional illustration",
                "image": char_data["image"],
                "source": char_data["source"]
            }
    
    # Try API sources
    data = jikan_lookup(name)
    if not data:
        data = wiki_lookup(name)
    
    if not data:
        # Enhanced fallback with more generic physical features
        return {
            "found": False,
            "prompt": name + ", original character design, detailed facial features, expressive eyes, distinctive hairstyle, unique outfit and clothing design, full body portrait, professional character concept art, intricate details, vibrant colors",
            "image": "",
            "source": "fallback"
        }
    
    return {
        "found": True,
        "prompt": data['desc'] + ", highly detailed character portrait, professional anime illustration",
        "image": data["image"],
        "source": data.get("source", "unknown")
    }

@app.get("/")
def root():
    return {
        "status": "Character Lookup API v2.0 - Enhanced Physical Descriptions",
        "endpoints": {
            "lookup": "/lookup?name=CHARACTER_NAME"
        },
        "manual_characters": list(MANUAL_CHARS.keys()),
        "features": [
            "Physical appearance extraction",
            "Multi-source lookup (Jikan, Wikipedia)",
            "Response caching",
            "Enhanced visual detail parsing"
        ]
    }
