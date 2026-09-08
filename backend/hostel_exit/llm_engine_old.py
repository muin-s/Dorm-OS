import os
import json
import threading
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

USE_REAL_LLM = os.getenv("USE_REAL_LLM", "false").lower() == "true"
MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"

_tokenizer = None
_model = None
_lock = threading.Lock()

# -------------------------
# FIX 2: SAFE MODEL LOADING
# -------------------------
def _load():
    global _tokenizer, _model

    _tokenizer = AutoTokenizer.from_pretrained(
        MODEL_ID,
        trust_remote_code=True,
        use_fast=False          # REQUIRED for Qwen 2.5
    )

    _model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        trust_remote_code=True,
        torch_dtype=torch.float32
    ).eval()


# -------------------------
# FIX 3: CRASH-PROOF RUNNER
# -------------------------
def run_llm(prompt: str) -> dict:
    # Fallback when LLM disabled
    if not USE_REAL_LLM:
        return {
            "intent": "REGULAR_EXIT",
            "reason": "Personal work",
            "leave_datetime": "2025-12-21T10:00:00",
            "return_datetime": "2025-12-21T18:00:00",
            "room_type": "4_seater",
            "emergency_contact": "9999999999"
        }

    # ---- SAFE INIT ----
    try:
        global _model
        if _model is None:
            with _lock:
                if _model is None:
                    print("Loading Qwen model (one-time)...")
                    _load()
    except Exception as e:
        print("LLM INIT FAILED:", e)
        return {
            "intent": "UNKNOWN",
            "error": "model_init_failed"
        }

    # ---- PROMPT FORMAT ----
    try:
        messages = [
            {
                "role": "system",
                "content": "Extract hostel exit details and return ONLY valid JSON."
            },
            {"role": "user", "content": prompt}
        ]

        formatted_prompt = _tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
    except Exception as e:
        print("PROMPT FORMAT FAILED:", e)
        formatted_prompt = prompt

    # ---- GENERATION ----
    try:
        inputs = _tokenizer(formatted_prompt, return_tensors="pt")
        with torch.no_grad():
            outputs = _model.generate(
                **inputs,
                max_new_tokens=256,
                temperature=0.1,
                do_sample=True,
                top_p=0.9
            )
    except Exception as e:
        print("GENERATION FAILED:", e)
        return {
            "intent": "UNKNOWN",
            "error": "generation_failed"
        }

    text = _tokenizer.decode(outputs[0], skip_special_tokens=True)
    print("RAW LLM TEXT:", text[:500])

    # ---- JSON EXTRACTION ----
    start = text.find("{")
    if start == -1:
        return {"intent": "UNKNOWN", "error": "no_json"}

    brace_count = 0
    end = start
    for i in range(start, len(text)):
        if text[i] == "{":
            brace_count += 1
        elif text[i] == "}":
            brace_count -= 1
            if brace_count == 0:
                end = i + 1
                break

    if brace_count != 0:
        return {"intent": "UNKNOWN", "error": "incomplete_json"}

    json_str = text[start:end]
    print("EXTRACTED JSON:", json_str)

    try:
        return json.loads(json_str)
    except Exception as e:
        print("JSON PARSE FAILED:", e)
        return {"intent": "UNKNOWN", "error": "json_parse_failed"}
