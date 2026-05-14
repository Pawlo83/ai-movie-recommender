import spacy
import torch
import os
import gc
import pickle
import numpy as np
from transformers import MarianMTModel, MarianTokenizer
from sentence_transformers import SentenceTransformer
from supabase import create_client
from .lang_configs import SUPABASE_URL, SUPABASE_KEY

# Stan Globalny
RESOURCES = {
    "supabase": None,
    "db_tags_list": [],
    "db_vectors": None,
    "valid_db_tags": set(),
    "similarity_model": None,
    "spacy_models": {},
    "is_initialized": False
}

def get_spacy_model(model_name):
    """Leniwe ładowanie modelu SpaCy."""
    if model_name not in RESOURCES["spacy_models"]:
        try:
            RESOURCES["spacy_models"][model_name] = spacy.load(model_name)
        except OSError:
            from spacy.cli import download
            download(model_name)
            RESOURCES["spacy_models"][model_name] = spacy.load(model_name)
    return RESOURCES["spacy_models"][model_name]

def initialize_tagger():
    """Inicjalizuje wszystkie ciężkie modele, bazę danych, a także ładuje dane z cached_vectors"""
    if RESOURCES["is_initialized"]:
        return

    print("[INFO] Inicjalizacja Semantic Taggera...")
    gc.collect()

    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Brak zmiennych środowiskowych SUPABASE.")

        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        RESOURCES["supabase"] = client

        response = client.table('tags').select('tag_name').execute()
        if response.data:
            live_db_tags = [item['tag_name'].lower() for item in response.data]

    except Exception as e:
        print(f"[ERROR] Supabase Init: {e}")
        live_db_tags = []

    try:
        sim_model = SentenceTransformer('paraphrase-MiniLM-L3-v2')
        RESOURCES["similarity_model"] = sim_model

        final_tags = []
        final_vectors = None
        cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'cached_vectors.pkl')
        if not os.path.exists(cache_path):
             cache_path = "cached_vectors.pkl"

        cached_tags_set = set()

        if os.path.exists(cache_path):
            print(f"[INFO] Znaleziono cache: {cache_path}. Wczytywanie...")
            with open(cache_path, "rb") as f:
                cached_data = pickle.load(f)
                final_tags = cached_data["texts"]
                final_vectors = cached_data["vectors"]
                cached_tags_set = set(final_tags)
        else:
            print("[WARN] Brak pliku cached_vectors.pkl! Aplikacja spróbuje policzyć wszystko (może wystąpić Timeout).")

        new_tags_to_compute = [tag for tag in live_db_tags if tag not in cached_tags_set]
        if new_tags_to_compute:
            print(f"[INFO] Wykryto {len(new_tags_to_compute)} nowych tagów w bazie. Doliczam wektory...")
            new_vectors = sim_model.encode(new_tags_to_compute, convert_to_numpy=True)
            
            if final_vectors is not None:
                final_tags.extend(new_tags_to_compute)
                final_vectors = np.concatenate((final_vectors, new_vectors), axis=0)
            else:
                final_tags = new_tags_to_compute
                final_vectors = new_vectors
        else:
            print("[INFO] Cache jest aktualny. Brak nowych tagów.")

        if final_vectors is not None:
             RESOURCES["db_vectors"] = torch.tensor(final_vectors)
        else:
             RESOURCES["db_vectors"] = None

        RESOURCES["db_tags_list"] = final_tags
        RESOURCES["valid_db_tags"] = set(final_tags)

    except Exception as e:
        print(f"[ERROR] SimModel Init: {e}")
        RESOURCES["db_tags_list"] = []

    RESOURCES["is_initialized"] = True
    print("[INFO] Tagger zakończył inicjalizację.")