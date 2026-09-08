import re

FILLER_WORDS = {
    "near me", "nearby", "close to", "around", "find me", "find",
    "search", "looking for", "need", "want", "please", "get me",
    "where is", "where can i", "i want", "i need", "show me",
    "available", "any", "some", "good", "best", "cheap"
}

def clean_query(query: str) -> str:
    q = query.lower().strip()
    for fw in FILLER_WORDS:
        q = q.replace(fw, " ")
    q = re.sub(r"\s+", " ", q).strip()
    return q

_model = None

BLOCKED_AMENITIES = {
    "place_of_worship", "temple", "theatre", "cinema",
    "college", "school", "university", "library",
    "bank", "atm", "hospital", "clinic", "fuel"
}

BLOCKED_NAME_KEYWORDS = {
    "hospital", "medical college", "igmc", "school",
    "temple", "vihar", "church", "masjid", "mandir",
    "theatre", "talkies", "movie", "college", "inpatient",
    "outpatient", "govt", "government"
}

def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def shop_to_text(shop):
    parts = []
    if shop.get("name"):
        parts.append(shop["name"])
    if shop.get("shop"):
        parts.append(shop["shop"])
    if shop.get("amenity"):
        parts.append(shop["amenity"])
    return " ".join(parts).lower()

def is_blocked_name(name):
    name_lower = (name or "").lower()
    return any(kw in name_lower for kw in BLOCKED_NAME_KEYWORDS)

def is_valid_shop(shop):
    if is_blocked_name(shop.get("name", "")):
        return False
    if shop.get("amenity") in BLOCKED_AMENITIES:
        return False
    if shop.get("shop"):
        return True
    if shop.get("amenity") in {"cafe", "restaurant", "fast_food", "pharmacy"}:
        return True
    return False

def deduplicate(shops):
    # Group by name, keep the closest one per name
    seen = {}
    for s in shops:
        name = s.get("name", "").strip().lower()
        if not name or name == "unnamed":
            continue
        dist = s.get("distance_km", 999)
        if name not in seen or dist < seen[name].get("distance_km", 999):
            seen[name] = s
    return list(seen.values())


COMMON_SHOP_WORDS = [
    "dairy", "bakery", "grocery", "pharmacy", "restaurant", "cafe",
    "electronics", "furniture", "stationery", "hardware", "medical",
    "chicken", "meat", "vegetables", "fruits", "clothes", "shoes",
    "mobile", "repair", "salon", "hotel", "sweet", "snacks", "juice",
    "tea", "coffee", "rice", "flour", "oil", "milk", "eggs", "bread",
    "fish", "mutton", "paneer", "tiffin", "food", "fast food"
]

def fuzzy_correct(query: str) -> str:
    try:
        from rapidfuzz import process, fuzz
        words = query.split()
        corrected = []
        for word in words:
            if len(word) < 4:
                corrected.append(word)
                continue
            match = process.extractOne(word, COMMON_SHOP_WORDS, scorer=fuzz.ratio)
            if match and match[1] >= 75:
                corrected.append(match[0])
            else:
                corrected.append(word)
        return " ".join(corrected)
    except Exception:
        return query

def rank_shops_bert(query, shops, top_k=10):
    query = clean_query(query)
    query = fuzzy_correct(query)
    shops = deduplicate(shops)
    filtered = [s for s in shops if is_valid_shop(s)]
    if not filtered:
        return []
    texts = [shop_to_text(s) for s in filtered]
    model = _get_model()
    from sentence_transformers import util
    q_emb = model.encode(query, convert_to_tensor=True)
    s_emb = model.encode(texts, convert_to_tensor=True)
    scores = util.cos_sim(q_emb, s_emb)[0]
    ranked = []
    for shop, score in zip(filtered, scores):
        score = float(score)
        if score >= 0.42:
            ranked.append({**shop, "nlp_score": score})
    ranked.sort(key=lambda x: (-x["nlp_score"], x.get("distance_km", 999)))
    return ranked[:top_k]
