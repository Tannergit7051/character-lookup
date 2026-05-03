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
CACHE_DURATION = 7200

def extract_physical_features(text, char_name):
    """Extract highly detailed physical appearance"""
    if not text:
        return char_name + ", detailed character design"
    
    appearance_keywords = [
        'hair', 'hairstyle', 'haircut', 'bangs', 'ponytail', 'braid', 'spiky', 'curly', 'straight', 'wavy',
        'blonde', 'brunette', 'black-haired', 'white-haired', 'silver', 'gray', 'red-haired', 'pink', 'blue',
        'eyes', 'eye color', 'pupils', 'gaze', 'blue eyes', 'green eyes', 'brown eyes', 'red eyes', 'yellow eyes',
        'face', 'facial', 'cheeks', 'jaw', 'chin', 'nose', 'mouth', 'lips', 'smile', 'grin', 'expression',
        'scar', 'scars', 'tattoo', 'marking', 'birthmark', 'whiskers', 'beard', 'mustache', 'freckles',
        'tall', 'short', 'height', 'build', 'physique', 'muscular', 'slim', 'slender', 'petite', 'athletic',
        'skin', 'complexion', 'pale', 'tan', 'dark', 'fair', 'light',
        'wears', 'wearing', 'dressed', 'outfit', 'clothing', 'costume', 'uniform', 'suit', 'dress', 'shirt',
        'jacket', 'coat', 'pants', 'boots', 'shoes', 'hat', 'cape', 'cloak', 'armor', 'robe', 'belt', 'gloves',
        'carries', 'holds', 'weapon', 'sword', 'staff', 'gun', 'wings', 'tail', 'horns', 'ears',
        'appearance', 'look', 'design', 'style', 'features', 'distinctive', 'signature', 'iconic'
    ]
    
    sentences = re.split(r'[.!?]+', text)
    visual_sentences = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence or len(sentence) < 10:
            continue
        sentence_lower = sentence.lower()
        visual_count = sum(1 for keyword in appearance_keywords if keyword in sentence_lower)
        
        if visual_count >= 1:
            visual_sentences.append(sentence)
            if len(visual_sentences) >= 8:
                break
    
    if visual_sentences:
        result = char_name + ", " + " ".join(visual_sentences)
    else:
        words = text.split()[:150]
        result = char_name + ", " + " ".join(words)
    
    result = re.sub(r'\s+', ' ', result)
    result = re.sub(r'\s*,\s*,\s*', ', ', result)
    return result

def jikan_lookup(name: str):
    cache_key = "jikan_" + name.lower()
    if cache_key in cache:
        cached_time, cached_data = cache[cache_key]
        if time.time() - cached_time < CACHE_DURATION:
            return cached_data
    
    url = "https://api.jikan.moe/v4/characters?q=" + name + "&limit=10"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
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
            if name_lower == char_name:
                best = char
                break
        
        if not best:
            for char in results:
                char_name = char.get("name", "").lower()
                name_parts = name_lower.split()
                if any(part in char_name for part in name_parts):
                    best = char
                    break
        
        if not best:
            best = results[0]
        
        char_name = best.get("name", name)
        about = best.get("about", "") or ""
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
    except:
        return None

def wiki_lookup(name: str):
    cache_key = "wiki_" + name.lower()
    if cache_key in cache:
        cached_time, cached_data = cache[cache_key]
        if time.time() - cached_time < CACHE_DURATION:
            return cached_data
    
    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + name.replace(" ", "_")
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return None
        data = r.json()
        if data.get("type") == "disambiguation":
            return None
        
        title = data.get("title", name)
        extract = data.get("extract", "")
        description = extract_physical_features(extract, title)
        
        result = {
            "title": title,
            "desc": description,
            "image": data.get("thumbnail", {}).get("source", ""),
            "source": "wikipedia"
        }
        
        cache[cache_key] = (time.time(), result)
        return result
    except:
        return None

# Ultra-detailed character database - Zero ambiguity descriptions
MANUAL_CHARS = {
    "rin tohsaka": {
        "title": "Rin Tohsaka",
        "desc": "Rin Tohsaka, long straight black hair reaching lower back with bangs framing face, bright aqua blue eyes with sharp determined gaze, fair porcelain skin, slender athletic build with subtle curves, height 159cm, wears red turtleneck sweater, black miniskirt, black thigh-high stockings with small gap of bare thigh visible, brown lace-up boots, distinctive red pendant necklace hanging at chest level, confident proud expression with slight smirk, tsundere personality showing through facial expression, from Fate/stay night anime series",
        "image": "",
        "source": "manual"
    },
    "yamato": {
        "title": "Yamato",
        "desc": "Yamato, extremely long white hair in thick ponytail reaching past waist with strands framing face and two red horn ornaments on sides of head, golden orange eyes, tall imposing height of 263cm, very muscular athletic build with defined abs and strong arms, large chest, tan skin, wears white sleeveless kimono-style top with red trim showing cleavage and midriff, hakama pants, sandals, thick shimenawa sacred rope tied around waist, carries large kanabo club weapon, red horns growing from head, fierce determined expression, daughter of Kaido from One Piece anime",
        "image": "",
        "source": "manual"
    },
    "rukia kuchiki": {
        "title": "Rukia Kuchiki",
        "desc": "Rukia Kuchiki, short black hair in bob cut with bangs, large expressive violet purple eyes, very pale white porcelain skin, petite small build, short height of 144cm, flat chest, wears black shihakusho Soul Reaper kimono uniform with white obi sash, white tabi socks, waraji sandals, carries katana zanpakuto sword at hip, serious composed expression with occasional soft smile, from Bleach anime series",
        "image": "",
        "source": "manual"
    },
    "marin kitagawa": {
        "title": "Marin Kitagawa",
        "desc": "Marin Kitagawa, long blonde hair reaching mid-back with pink gradient tips at ends, bright cheerful pink-red eyes, fair skin with healthy glow, curvy athletic build with large chest and slim waist, height 164cm, often wears trendy gyaru fashion - cropped tops showing midriff, short skirts or shorts, thigh-high stockings, platform shoes, colorful painted nails, multiple ear piercings with dangling earrings, bright energetic smile, extroverted bubbly expression, from My Dress-Up Darling anime series",
        "image": "",
        "source": "manual"
    },
    "rias gremory": {
        "title": "Rias Gremory",
        "desc": "Rias Gremory, extremely long crimson red hair flowing past hips in loose waves, bright blue-green aqua eyes, flawless porcelain skin, voluptuous curvaceous build with very large chest and wide hips, tall height of 172cm, typically wears Kuoh Academy girls uniform - white shirt with red tie, black skirt, or revealing outfits showing cleavage, regal elegant posture, gentle kind smile with underlying confidence, devil heiress with noble bearing, from High School DxD anime series",
        "image": "",
        "source": "manual"
    },
    "yoko littner": {
        "title": "Yoko Littner",
        "desc": "Yoko Littner, very long straight red-orange hair reaching past waist with yellow flame-like hair clip on right side, golden amber yellow eyes, tan sun-kissed skin, tall athletic build with very large chest and toned abs, height 164cm, wears extremely revealing outfit - tiny red and black flame-pattern bikini top, very short black shorts with belt, thigh-high red and black striped stockings, knee-high boots, long fingerless gloves, pink scarf around neck, skull hair ornament, carries large sniper rifle, confident bold expression, from Gurren Lagann anime series",
        "image": "",
        "source": "manual"
    },
    "rio futaba": {
        "title": "Rio Futaba",
        "desc": "Rio Futaba, shoulder-length straight dark blue-black hair with bangs, dark brown eyes behind black-rimmed rectangular glasses, pale fair skin, slender petite build with subtle curves, average height, wears Minegahara High School uniform - white shirt, red ribbon tie, gray skirt, dark thigh-high socks, brown loafers, often seen in white lab coat for science club, serious intellectual expression with occasional soft smile, analytical observant gaze, from Rascal Does Not Dream of Bunny Girl Senpai anime series",
        "image": "",
        "source": "manual"
    },
    "nami": {
        "title": "Nami",
        "desc": "Nami, long wavy orange hair reaching mid-back often in loose style, large expressive brown eyes, fair skin with slight tan, slim curvy athletic build with very large chest and defined waist, tall height of 170cm, typically wears revealing bikini tops or cropped tank tops showing ample cleavage and midriff, low-rise jeans or very short skirts, high heels or sandals, distinctive blue and white striped pinwheel tattoo on left shoulder and arm, gold bracelets, carries orange and blue Clima-Tact staff, confident flirtatious smile, navigator of Straw Hat Pirates from One Piece anime",
        "image": "",
        "source": "manual"
    },
    "linia dedoldia": {
        "title": "Linia Dedoldia",
        "desc": "Linia Dedoldia, short wild black hair in messy spiky style, yellow cat-like slit pupils in golden eyes, tan bronze skin, athletic toned muscular build, cat ears on top of head covered in black fur, long black cat tail, wears minimal tribal clothing - brown cloth chest wraps, short brown skirt or loincloth, leather straps and wraps on arms and legs, barefoot or simple sandals, sharp canine teeth visible when grinning, feral energetic expression, beast race warrior from Mushoku Tensei anime series",
        "image": "",
        "source": "manual"
    },
    "ghislaine dedoldia": {
        "title": "Ghislaine Dedoldia",
        "desc": "Ghislaine Dedoldia, long wild silver-white hair in untamed mane-like style, sharp yellow cat-like slit pupils in golden eyes, dark tan bronze skin, extremely muscular powerful build with defined abs and strong arms, very tall imposing height, large chest, beast ears on top of head covered in silver fur, long silver cat tail, wears minimal revealing outfit - leather bikini top barely containing chest, fur loincloth bottom, leather straps crossed over torso, metal arm guards, barefoot, multiple scars on body including large cross-shaped scar on abdomen, eyepatch over left eye, fierce intimidating expression with sharp fangs visible, carries large sword, beast race swordmaster from Mushoku Tensei anime series",
        "image": "",
        "source": "manual"
    },
    "eris boreas greyrat": {
        "title": "Eris Boreas Greyrat",
        "desc": "Eris Boreas Greyrat, long bright crimson red hair in wild flowing style reaching lower back, sharp fierce golden amber eyes, fair skin with slight tan from training, athletic muscular build with toned abs and strong limbs, medium height, typically wears adventurer outfit - white sleeveless tunic showing arms, brown leather pants, tall brown boots, sword belt at waist, red cape or cloak, fierce determined expression with aggressive energy, tsundere personality visible in posture, from Mushoku Tensei anime series",
        "image": "",
        "source": "manual"
    },
    "sylphiette": {
        "title": "Sylphiette",
        "desc": "Sylphiette, short white hair in bob cut with slight green tint, bright emerald green eyes, very fair pale skin, petite slender build, short height, pointed elf ears, wears simple adventurer clothing - white blouse, brown vest, green skirt or pants, brown boots, gentle kind expression with shy demeanor, half-elf from Mushoku Tensei anime series",
        "image": "",
        "source": "manual"
    },
    "roxy migurdia": {
        "title": "Roxy Migurdia",
        "desc": "Roxy Migurdia, shoulder-length blue hair with bangs, large bright blue eyes, very pale porcelain skin, petite small build, very short height of 140cm appearing childlike, flat chest, wears blue magician robes with white trim and pointed blue wizard hat with white band, brown boots, carries wooden staff, serious composed expression for age, demon race Migurd tribe with slightly pointed ears, from Mushoku Tensei anime series",
        "image": "",
        "source": "manual"
    },
    "asuna yuuki": {
        "title": "Asuna Yuuki",
        "desc": "Asuna Yuuki, long straight chestnut orange-brown hair reaching lower back with bangs, large hazel brown eyes, fair porcelain skin, slender athletic build with curves, height 168cm, in SAO wears Knights of the Blood red and white uniform - white and red dress-like top with armor plating, white skirt with red accents, white and red thigh-high boots, carries rapier sword named Lambent Light, determined confident expression, from Sword Art Online anime series",
        "image": "",
        "source": "manual"
    },
    "mikasa ackerman": {
        "title": "Mikasa Ackerman",
        "desc": "Mikasa Ackerman, short black hair in bob cut, dark gray eyes with intense focused gaze, pale fair skin, athletic muscular build with visible abs and toned arms, height 170cm, wears brown cropped jacket over white shirt, white pants, brown boots, red scarf wrapped around neck gifted by Eren, green Survey Corps cape with Wings of Freedom emblem, carries dual blades and ODM gear, stoic serious expression with protective demeanor, from Attack on Titan anime series",
        "image": "",
        "source": "manual"
    },
    "zero two": {
        "title": "Zero Two",
        "desc": "Zero Two, long pink hair reaching past waist in wild flowing style with distinctive red horns growing from head, bright pink-red eyes with intense gaze, fair smooth skin, tall curvy athletic build with large chest, height 170cm, wears red and white skin-tight plugsuit pilot uniform with honeycomb pattern showing curves, white stockings, red headband, fanged teeth visible when smiling, aggressive confident expression, klaxosaur-human hybrid from Darling in the Franxx anime series",
        "image": "",
        "source": "manual"
    },
    "mai sakurajima": {
        "title": "Mai Sakurajima",
        "desc": "Mai Sakurajima, long straight black hair reaching lower back, sharp dark purple-blue eyes, fair porcelain skin, slender tall build with subtle curves, height 165cm, wears Minegahara High School uniform - white shirt, red ribbon tie, black skirt, black thigh-high stockings, brown loafers, famous for bunny girl outfit - black leotard with white collar and cuffs, black pantyhose, bunny ears headband, serious mature expression with underlying kindness, from Rascal Does Not Dream of Bunny Girl Senpai anime series",
        "image": "",
        "source": "manual"
    },
    "raphtalia": {
        "title": "Raphtalia",
        "desc": "Raphtalia, long brown hair in flowing style reaching lower back, large expressive brown eyes, fair skin with slight tan, tall athletic build as adult form height 160cm, large fluffy tanuki raccoon ears on head, large fluffy tanuki tail, wears white and red adventurer outfit - white shirt with red vest, red skirt, brown leather belt and straps, brown boots, carries katana sword, determined loyal expression, demi-human tanuki from Rising of the Shield Hero anime series",
        "image": "",
        "source": "manual"
    },
    "filo": {
        "title": "Filo",
        "desc": "Filo, short blonde hair in twin drill curls on sides, large bright blue eyes, very fair skin with rosy cheeks, child-like petite build in human form, wears simple white dress with pink ribbon, no shoes, large angelic white wings can sprout from back, can transform into giant pink Filolial bird, cheerful energetic innocent expression, from Rising of the Shield Hero anime series",
        "image": "",
        "source": "manual"
    },
    "nezuko kamado": {
        "title": "Nezuko Kamado",
        "desc": "Nezuko Kamado, long black hair with orange-red gradient tips reaching waist in wavy style with side bangs, bright pink eyes that turn red when demon powers active, fair porcelain skin, petite slender build, short height of 153cm, wears pink kimono with hemp leaf pattern and dark brown haori jacket over it, red obi sash, barefoot or simple sandals, bamboo muzzle covering mouth held by red ribbon, demon with sharp fangs and claw-like nails, pink flame-like marks appear on face when using powers, gentle kind expression despite being demon, from Demon Slayer anime series",
        "image": "",
        "source": "manual"
    },
    "shinobu kocho": {
        "title": "Shinobu Kocho",
        "desc": "Shinobu Kocho, short black hair in bob cut with purple gradient tips and butterfly-shaped hair ornament, large purple-pink gradient eyes, very fair porcelain skin, petite small build, short height of 151cm, wears Demon Slayer Corps uniform - black gakuran-style top with gold buttons, white butterfly-patterned haori jacket with purple and pink gradients, black hakama pants, dark purple shin-high socks, carries unique insect-themed katana sword, gentle smile that hides darker emotions, Insect Hashira from Demon Slayer anime series",
        "image": "",
        "source": "manual"
    }
}

@app.get("/lookup")
def lookup(name: str):
    """Main character lookup endpoint"""
    name_clean = name.lower().strip()
    
    # Exact match in manual DB
    if name_clean in MANUAL_CHARS:
        return {
            "found": True,
            "prompt": MANUAL_CHARS[name_clean]["desc"],
            "image": MANUAL_CHARS[name_clean]["image"],
            "source": MANUAL_CHARS[name_clean]["source"]
        }
    
    # Partial match in manual DB
    for key, char_data in MANUAL_CHARS.items():
        if name_clean in key or key in name_clean:
            # Check if it's a close match
            name_parts = name_clean.split()
            key_parts = key.split()
            if any(part in key_parts for part in name_parts):
                return {
                    "found": True,
                    "prompt": char_data["desc"],
                    "image": char_data["image"],
                    "source": char_data["source"]
                }
    
    # Try API sources
    data = jikan_lookup(name)
    if not data:
        data = wiki_lookup(name)
    
    if not data:
        return {
            "found": False,
            "prompt": name + ", original character design, detailed facial features with large expressive eyes, distinctive hairstyle with specific hair color, unique clothing and outfit design with multiple accessories, full body character portrait, professional anime illustration style, intricate costume details, vibrant color palette, sharp clear details",
            "image": "",
            "source": "fallback"
        }
    
    return {
        "found": True,
        "prompt": data['desc'],
        "image": data["image"],
        "source": data.get("source", "unknown")
    }

@app.get("/")
def root():
    return {
        "status": "Character Lookup API v4.0 - Ultra Detailed Database",
        "manual_db_size": len(MANUAL_CHARS),
        "manual_characters": sorted(list(MANUAL_CHARS.keys())),
        "featured_series": [
            "Fate/stay night",
            "One Piece", 
            "Bleach",
            "My Dress-Up Darling",
            "High School DxD",
            "Gurren Lagann",
            "Bunny Girl Senpai",
            "Mushoku Tensei",
            "Sword Art Online",
            "Attack on Titan",
            "Darling in the Franxx",
            "Shield Hero",
            "Demon Slayer"
        ]
    }
