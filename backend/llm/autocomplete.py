import os
import requests
import re
import json


def get_autocomplete_suggestions(query: str):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found")
        return []

    endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=" + api_key

    prompt = (
        "You are helping hostel students search products and nearby shops. "
        "Given a partial query, suggest 5 short autocomplete search phrases. "
        "Return ONLY a JSON array of strings. No explanation. "
        "Query: \"" + query + "\""
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 200}
    }

    try:
        res = requests.post(endpoint, json=payload, timeout=15)
        res.raise_for_status()
        content = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        content = re.sub(r"^```json\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
        return json.loads(content)
    except Exception as e:
        print("Autocomplete LLM error:", e)
        return []
