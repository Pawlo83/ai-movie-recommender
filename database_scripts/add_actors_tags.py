import requests
from datetime import datetime, timedelta, timezone
from supabase import create_client, Client
import time
import os
from dotenv import load_dotenv

# Skrypt uzupełniający do process_films, który dodaje top 5 aktorów z danego filmu jako tagi. 

# --- KONFIGURACJA ---
load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") 

# Inicjalizacja klienta Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_top_actors(tmdb_id):
    # Pobiera listę 5 głównych aktorów z TMDB API

    # Konstrukcja zapytania do endpointu /credits
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/credits?api_key={TMDB_API_KEY}"
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"TMDB Error: {response.status_code}")
            return []
            
        data = response.json()
        # Sprawdzenie czy w odpowiedzi jest klucz 'cast'
        if 'cast' not in data:
            return []

        # Sortujemy po 'order' i bierzemy top 5
        top_cast = sorted(data['cast'], key=lambda x: x['order'])[:5]
        
        # Zwracamy tylko imiona i nazwiska
        return [actor['name'] for actor in top_cast]
        
    except Exception as e:
        print(f"Błąd połączenia z TMDB: {e}")
        return []

def add_tag_to_movie(film_id, tag_name):
    # Dodaje tag do bazy (jeśli nie istnieje) i przypisuje do filmu
    
    # Normalizacja: małe litery i usunięcie spacji
    clean_tag_name = tag_name.strip().lower()

    try:
        # 1. Sprawdź czy tag istnieje
        existing_tag = supabase.table('tags').select('id').eq('tag_name', clean_tag_name).execute()
        
        if existing_tag.data:
            # Jeśli istnieje, pobierz jego ID
            tag_id = existing_tag.data[0]['id']
        else:
            # 2. Jeśli nie istnieje, utwórz nowy rekord w tabeli 'tags'
            new_tag = supabase.table('tags').insert({"tag_name": clean_tag_name}).execute()
            tag_id = new_tag.data[0]['id']

        # 3. Przypisz tag do filmu w tabeli łączącej 'films_tags'
        try:
            supabase.table('films_tags').insert({
                "film_id": film_id,
                "tag_id": tag_id
            }).execute()
            return True # Sukces (nowe powiązanie)
        except Exception:
            return False # Już było

    except Exception as e:
        print(f"Błąd bazy danych dla '{tag_name}': {e}")
        return False

def main():
    print("Rozpoczynam uzupełnianie aktorów dla WSZYSTKICH filmów w bazie...")

    # 1. Pobieramy WSZYSTKIE filmy, które mają tmdb_id
    try:
        response = supabase.table('films') \
            .select('id, name, tmdb_id') \
            .neq('tmdb_id', 'null') \
            .execute()
        
        all_films = response.data
    except Exception as e:
        print(f"Błąd pobierania filmów: {e}")
        return

    total_films = len(all_films)
    if not all_films:
        print("Baza filmów z ID TMDB jest pusta.")
        return

    print(f"Znaleziono {total_films} filmów do przetworzenia.\n")

    # 2. Pętla po wszystkich filmach
    for index, film in enumerate(all_films, 1):
        print(f"[{index}/{total_films}] 🎬 {film['name']} (TMDB ID: {film['tmdb_id']})...")
        
        # Pobranie aktorów z zewnętrznego API
        actors = get_top_actors(film['tmdb_id'])
        
        if not actors:
            print("Brak danych o obsadzie.")
        else:
            added_count = 0
            # Pętla po każdym znalezionym aktorze
            for actor_name in actors:
                # Próba zapisu do bazy
                if add_tag_to_movie(film['id'], actor_name):
                    added_count += 1
            
            if added_count > 0:
                print(f"Dodano {added_count} nowych aktorów.")
            else:
                print("Aktorzy już przypisani.")
        

    print("\nZakończono aktualizację całej bazy.")

if __name__ == "__main__":
    main()