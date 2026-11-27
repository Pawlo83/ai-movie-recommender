import os
import pickle
from dotenv import load_dotenv
from supabase import create_client
from sentence_transformers import SentenceTransformer

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

MODEL_NAME = "paraphrase-MiniLM-L3-v2"
CACHE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "backend", "cached_vectors.pkl"
)

def generate_vector_cache():
    print("--- START GENEROWANIA CACHE ---")
    
    print("[1/4] Łączenie z bazą danych Supabase...")
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("BŁĄD: Brak SUPABASE_URL lub SUPABASE_KEY w pliku .env")
        return

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    response = supabase.table('tags').select('tag_name').execute()
    
    if not response.data:
        print("BŁĄD: Baza danych jest pusta lub nie udało się pobrać danych.")
        return

    texts = [item['tag_name'].lower() for item in response.data]
    print(f"      Pobrano {len(texts)} rekordów.")

    print("[2/4] Ładowanie modelu SentenceTransformer (to może chwilę potrwać)...")
    model = SentenceTransformer(MODEL_NAME)

    print("[3/4] Generowanie wektorów (nie wyłączaj komputera)...")
    vectors = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)

    print(f"[4/4] Zapisywanie do pliku '{CACHE_PATH}'...")
    data_to_save = {
        "model": MODEL_NAME,
        "dim": int(vectors.shape[1]),
        "texts": texts,
        "vectors": vectors,
    }

    with open(CACHE_PATH, "wb") as f:
        pickle.dump(data_to_save, f, protocol=4)

    print(f"\nSUKCES! Plik '{CACHE_PATH}' został utworzony.")
    print("Cache jest wersjonowany w repo - commitnij go, żeby trafił na Render.")

if __name__ == "__main__":
    generate_vector_cache()