import requests
from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Skrypt uzupełniający do process_films, który dodaje tmdb_id do istniejących już w bazie filmów.

# --- KONFIGURACJA ---
load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") 

# Inicjalizacja klienta bazy danych
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def check_director_match(tmdb_id, local_director):
    # Sprawdza, czy reżyser filmu z TMDB zgadza się z reżyserem w naszej bazie lokalnej.
    # Wymaga dodatkowego zapytania do API o szczegóły filmu (credits).
    if not local_director:
        return True # Jeśli nie mamy reżysera w bazie, ufamy po prostu tytułowi/roku

    # URL do pobrania obsady (credits) dla konkretnego ID filmu
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={TMDB_API_KEY}&append_to_response=credits"
    try:
        data = requests.get(url).json()
        
        # Wyciągamy reżysera z TMDB
        tmdb_director = "Unknown"
        if 'credits' in data:
            for crew in data['credits']['crew']:
                if crew['job'] == 'Director':
                    tmdb_director = crew['name']
                    break
        
        # Porównanie (proste sprawdzanie czy nazwisko zawiera się w stringu)
        # Normalizacja: małe litery i usunięcie białych znaków
        local_norm = local_director.lower().strip()
        tmdb_norm = tmdb_director.lower().strip()
        
        if local_norm in tmdb_norm or tmdb_norm in local_norm:
            return True
        else:
            print(f"Konflikt reżyserów. Baza: '{local_director}' vs TMDB: '{tmdb_director}'")
            return False

    except Exception:
        return False

def get_tmdb_id_verified(title, release_date, director):
    
    # Szuka ID filmu i weryfikuje reżysera.

    if not title:
        return None
        
    year_param = ""
    if release_date and len(release_date) >= 4:
        year = release_date.split('-')[0]
        year_param = f"&primary_release_year={year}"

    # Wyszukiwanie podstawowe
    search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={title}{year_param}&language=pl-PL"
    
    try:
        response = requests.get(search_url)
        data = response.json()
        
        # Jeśli brak wyników wyszukiwania, przerywamy
        if not data.get('results'):
            print(f"   ❌ Nie znaleziono w wyszukiwarce: {title}")
            return None

        # Pętla po wynikach i weryfikacja
        # Sprawdzamy np. pierwsze 3 wyniki wyszukiwania (bo czasem właściwy film jest drugi)
        for result in data['results'][:3]:
            candidate_id = result['id']
            candidate_title = result['title']
            
            # Dodatkowe zapytanie weryfikujące reżysera
            if check_director_match(candidate_id, director):
                print(f"Znaleziono i zweryfikowano: '{candidate_title}' (ID: {candidate_id})")
                return candidate_id
        
        print(f"Znaleziono tytuły, ale żaden reżyser nie pasował do: '{director}'")
        return None
            
    except Exception as e:
        print(f"Błąd API: {e}")
        return None

def main():
    print("Rozpoczynam uzupełnianie tmdb_id (Tryb Dokładny: Reżyser)")

    # Pobieramy z bazy tylko te filmy, które NIE mają jeszcze przypisanego tmdb_id (is null)
    try:
        response = supabase.table('films') \
            .select('id, name, release_date, director') \
            .is_('tmdb_id', 'null') \
            .execute()
        films_to_update = response.data
    except Exception as e:
        print(f"Błąd Supabase: {e}")
        return

    if not films_to_update:
        print("Brak filmów do aktualizacji.")
        return

    print(f"Do przetworzenia: {len(films_to_update)} filmów.\n")
    
    # Główna pętla przetwarzająca filmy jeden po drugim
    for film in films_to_update:
        print(f"Przetwarzam: '{film['name']}' ({film['director']})...")
        
        # Próba znalezienia ID z weryfikacją
        found_id = get_tmdb_id_verified(film['name'], film['release_date'], film['director'])
        
        # Jeśli znaleziono ID, aktualizujemy rekord w bazie
        if found_id:
            try:
                supabase.table('films').update({'tmdb_id': found_id}).eq('id', film['id']).execute()
                print("Zapisano.")
            except Exception as e:
                print(f"Błąd zapisu: {e}")
        

if __name__ == "__main__":
    main()