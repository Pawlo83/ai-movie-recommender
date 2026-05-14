import os
import pickle
from dotenv import load_dotenv
from supabase import create_client
from sentence_transformers import SentenceTransformer

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

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
    model = SentenceTransformer('paraphrase-MiniLM-L3-v2')

    print("[3/4] Generowanie wektorów (nie wyłączaj komputera)...")
    vectors = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)

    print("[4/4] Zapisywanie do pliku 'cached_vectors.pkl'...")
    data_to_save = {
        "texts": texts,
        "vectors": vectors
    }
    
    with open("cached_vectors.pkl", "wb") as f:
        pickle.dump(data_to_save, f)
    
    print("\nSUKCES! Plik 'cached_vectors.pkl' został utworzony.")
    print("Teraz wykonaj: git add cached_vectors.pkl && git commit -m 'Add cache' && git push")

if __name__ == "__main__":
    generate_vector_cache()