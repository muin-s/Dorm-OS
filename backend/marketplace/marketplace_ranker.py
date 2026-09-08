import os
import requests
import json
import re

from marketplace.category_utils import (
    detect_category_from_query,
    is_pure_category_query
)

API_KEY = os.getenv("GEMINI_API_KEY")
ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"



SEMANTIC_EXPANSION = {
    "furniture": ["table", "chair", "desk", "bed", "shelf", "cupboard", "rack", "stool"],
    "electronics": ["laptop", "phone", "mobile", "charger", "earphones", "headphones", "cable", "tablet", "keyboard", "mouse"],
    "food": ["tiffin", "snacks", "biscuit", "chocolate", "noodles", "maggi", "chips", "juice", "drink"],
    "books": ["textbook", "novel", "notebook", "register", "copy", "notes"],
    "clothes": ["shirt", "tshirt", "jeans", "shoes", "sandals", "jacket", "hoodie"],
    "sports": ["cricket", "football", "badminton", "racket", "bat", "ball", "kit"],
    "stationery": ["pen", "pencil", "eraser", "marker", "highlighter", "stapler"],
    "appliances": ["fan", "heater", "iron", "kettle", "lamp", "bulb", "extension"],
    "cycles": ["bicycle", "cycle", "bike", "scooter"],
}

def expand_query(query: str) -> str:
    q = query.lower()
    extras = []
    for category, words in SEMANTIC_EXPANSION.items():
        if category in q:
            extras.extend(words)
        for word in words:
            if word in q:
                extras.append(category)
                extras.extend(words)
                break
    if extras:
        return q + " " + " ".join(set(extras))
    return q

def _call_llm(prompt: str):
    """
    Calls LLM and returns text safely.
    """

    if not API_KEY:
        raise RuntimeError("API_KEY not set")

    if not API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set")

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 200}
    }

    try:
        resp = requests.post(ENDPOINT, json=payload, timeout=25)
        resp.raise_for_status()
        content = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print("LLM marketplace ranking failed:", e)
        return None

    # clean json block if wrapped in fences
    content = content.strip()
    content = re.sub(r"^```(?:json)?", "", content)
    content = re.sub(r"```$", "", content)

    try:
        return json.loads(content)
    except Exception as e:
        print("LLM JSON parse failed:", e)
        print("RAW LLM:", content)
        return None


def rank_marketplace_items(query, items, top_k=15):
    """
    Rank items using LLM semantic reasoning with strong defaults fallback.
    """

    if not query or not items:
        return []

    # build list for LLM
    item_list = []
    for i in items:
        item_list.append({
            "id": i.id,
            "description": i.description or "",
            "category": i.category or "",
            "price": i.price,
        })

    prompt = f"""
You are ranking marketplace products for a search engine.

User search query:
"{query}"

Here are the available items (JSON list):
{json.dumps(item_list, ensure_ascii=False)}

Task:
Rank items by relevance to the user query.

Rules:
- consider meaning, not just keywords
- category understanding matters
- match intent (e.g., "cricket" -> sports)
- if nothing matches well, return empty list
- DO NOT invent new products

Return ONLY valid JSON like:
[
 {{ "id": 3, "score": 0.92 }},
 {{ "id": 7, "score": 0.75 }}
]
"""

    llm_result = _call_llm(prompt)

    # if LLM fails → fallback keyword search
    if not llm_result or not isinstance(llm_result, list):
        print("LLM ranking unavailable, using keyword fallback.")
        q = query.lower()

        ranked = []
        for i in items:
            text = (i.description or "").lower()
            score = sum(w in text for w in q.split())
            ranked.append((score, i))

        ranked.sort(key=lambda x: -x[0])

        return [
            {
                "id": i.id,
                "description": i.description,
                "category": i.category,
                "image_url": i.image_url,
                "contact_info": i.contact_info,
                "price": i.price,
                "status": i.status,
                "seller_id": i.seller_id,
                "score": score
            }
            for score, i in ranked[:top_k]
        ]

    # map scores back to real objects
    id_to_item = {i.id: i for i in items}

    results = []
    for entry in llm_result:
        iid = entry.get("id")
        score = entry.get("score", 0)

        if iid not in id_to_item:
            continue

        item = id_to_item[iid]

        results.append({
            "id": item.id,
            "description": item.description,
            "category": item.category,
            "image_url": item.image_url,
            "contact_info": item.contact_info,
            "price": item.price,
            "status": item.status,
            "seller_id": item.seller_id,
            "semantic_score": score
        })

    return results[:top_k]
