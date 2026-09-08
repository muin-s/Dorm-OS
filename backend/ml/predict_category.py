import os
import re
import joblib
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# ---------- NLP TOOLS (lightweight) ----------
_stop_words = None
_lemmatizer = None

def _init_nlp():
    global _stop_words, _lemmatizer
    if _stop_words is None:
        _stop_words = set(stopwords.words("english"))
    if _lemmatizer is None:
        _lemmatizer = WordNetLemmatizer()

# ---------- MODEL (lazy loaded) ----------
_model = None

BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "issue_category_svm.pkl")

def _get_model():
    global _model
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError("❌ SVM model not found. Train model first.")
        _model = joblib.load(MODEL_PATH)
    return _model

# ---------- TEXT CLEANING ----------
def clean_text(text: str) -> str:
    _init_nlp()
    text = text.lower()
    text = re.sub(r"[^a-zA-Z ]", " ", text)
    tokens = text.split()
    tokens = [
        _lemmatizer.lemmatize(w)
        for w in tokens
        if w not in _stop_words
    ]
    return " ".join(tokens)

# ---------- PREDICTION ----------
def predict_category(description: str) -> str:
    model = _get_model()
    cleaned = clean_text(description)
    prediction = model.predict([cleaned])
    return prediction[0]
