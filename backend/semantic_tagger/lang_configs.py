import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Czarna lista tagów
BLOCKED_TAGS = {
    "wanted", "movie", "movies", "film", "films", "cinema",
    "watch", "see", "looking", "search", "like", "liked",
    "good", "best"
}

# Konfiguracje językowe
LANG_CONFIGS = {
    "pl": {
        "model_name": "pl_core_news_lg",
        "negation_triggers": [
            "nie", "bez", "brak", "żaden", "ani", "zero", "niechęć", "odrzucam", "wykluczony", "wykluczyć"
        ],
        "intensifiers": ["bardzo", "mega", "strasznie", "niezwykle", "dużo", "totalnie"],
        "adverb_modifiers": {
            "dużo": 0.4, "strasznie": 0.3, "niezwykle": 0.3,
            "koniecznie": 0.4, "tylko": 0.45, "musi": 0.45, "uwielbiam": 0.3,
            "mnóstwo": 0.25, "sporo": 0.25, "pełno": 0.25, "zdecydowanie": 0.2,
            "wielki": 0.2, "wysoki": 0.2, "totalnie": 0.3,
            "trochę": -0.30, "lekko": -0.25, "nieco": -0.20, "mało": -0.35,
            "ewentualnie": -0.15, "może": -0.1, "czasami": -0.1, "tło": -0.2
        }
    },
    "en": {
        "model_name": "en_core_web_sm",
        "negation_triggers": [
            "not", "no", "never", "without", "lack", "none", "neither", "nor", "avoid", "exclude", "don't", "won't",
            "cant"
        ],
        "intensifiers": ["very", "really", "extremely", "highly", "huge", "absolutely", "so", "too"],
        "adverb_modifiers": {
            "very": 0.3, "really": 0.3, "extremely": 0.35, "highly": 0.3,
            "absolutely": 0.4, "must": 0.4, "only": 0.4, "huge": 0.25,
            "lot": 0.25, "many": 0.25, "much": 0.25, "definitely": 0.4, "total": 0.3,
            "little": -0.35, "bit": -0.3, "slightly": -0.25, "barely": -0.3,
            "hardly": -0.25, "few": -0.2, "maybe": -0.1, "background": -0.2,
            "somewhat": -0.15
        }
    }
}