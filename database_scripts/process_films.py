import requests
import json
import argparse
import os
from supabase import create_client, Client
from openai import OpenAI
import urllib.parse
from dotenv import load_dotenv

# Skrypt podzielony na dwie flagi:
# 1. --movies
# Pobiera "keywords" z TMDB API i wysyła prompt do OPENAI API w celu otagowania filmów.
# 2. --save
# Zapisuje filmy do bazy danych Supabase z podanego jako argument pliku JSON.

# Konfiguracja
load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") 
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Inicjalizacja klientów
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
client_ai = OpenAI(api_key=OPENAI_API_KEY)

def get_tmdb_data(movie_input):
    # Pobiera dane filmu. Obsługuje format 'Tytuł' LUB 'Tytuł|Rok' 
    # Sprawdzamy, czy podano rok (rozdzielony znakiem |)
    if "|" in movie_input:
        movie_name, movie_year = movie_input.split("|")
        print(f"TMDB: Szukam '{movie_name}' z roku {movie_year}")
        # Dodajemy parametr primary_release_year do zapytania
        encoded_name = urllib.parse.quote(movie_name)
        search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={encoded_name}&primary_release_year={movie_year}"
    else:
        movie_name = movie_input
        print(f"TMDB: Szukam '{movie_name}' (bez konkretnego roku)")
        encoded_name = urllib.parse.quote(movie_name)
        search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={encoded_name}"

    try:
        # Wysłanie żądania do API
        search_res = requests.get(search_url).json()
    except Exception as e:
        print(f"Błąd połączenia z TMDB: {e}")
        return None
    
    if not search_res.get('results'):
        print(f"Nie znaleziono filmu w TMDB: {movie_name}")
        return None
    
    movie_id = search_res['results'][0]['id']
    
    # Pobranie szczegółów filmu wraz z obsadą (credits) i słowami kluczowymi
    details_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&append_to_response=credits,keywords"
    data = requests.get(details_url).json()
    
    # Ekstrakcja reżysera z listy 'crew'
    directors_list = []
    if 'credits' in data:
        for crew in data['credits']['crew']:
            if crew['job'] == 'Director':
                directors_list.append(crew['name'])

    # Łączenie nazwisk reżyserów w jeden string
    director = ", ".join(directors_list) if directors_list else "Unknown"
            
    # Ekstrakcja słów kluczowych TMDB
    tmdb_keywords = []
    if 'keywords' in data:
        tmdb_keywords = [k['name'] for k in data['keywords']['keywords']]
    
    return {
        "title": data['title'],
        "release_date": data.get('release_date', '1900-01-01'),
        "director": director,
        "overview": data.get('overview', ''),
        "tmdb_tags": tmdb_keywords
    }

def get_ai_tags(tmdb_data):
    # Wysyła zapytanie do OpenAI i zwraca JSON z podziałem na tagi
    print(f"AI: Generuję tagi dla '{tmdb_data['title']}'")

    prompt = f"""
    Jesteś ekspertem filmowym. Masz dane filmu:
    Tytuł: {tmdb_data['title']}
    Opis: {tmdb_data['overview']}
    Tagi źródłowe z TMDB: {', '.join(tmdb_data['tmdb_tags'])}
    
    Zadanie:
    1. Przeanalizuj film.
    2. Z listy "Tagi źródłowe z TMDB" wybierz wszystkie i umieść je w polu "tmdb_tags".
    3. Wymyśl w języku angielskim NOWE tagi (gatunek, klimat, motywy), których brakuje, i umieść je w polu "ai_tags" - postaraj się aby były różne od tych z tmdb (np. nie dodawaj sci-fi jeżeli z tmdb mamy science fiction).
    4. Zwróć dane jako CZYSTY JSON (bez formatowania Markdown).
    5. Format JSON ma wyglądać dokładnie tak:
    {{
        "name": "{tmdb_data['title']}",
        "release_date": "{tmdb_data['release_date']}",
        "director": "{tmdb_data['director']}",
        "tmdb_tags": ["tu wpisz wybrane tagi z listy TMDB"],
        "ai_tags": ["tu wpisz nowe tagi od AI"]
    }}
    """

    try:
        # Wywołanie modelu
        response = client_ai.chat.completions.create(
            model="gpt-4o-mini", # Używamy modelu mini
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        content = response.choices[0].message.content
        # Czyszczenie odpowiedzi z markdowna (gdyby AI dodało ```json)
        clean_content = content.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_content)
    except Exception as e:
        print(f"Błąd AI dla filmu {tmdb_data['title']}: {e}")
        return None

def save_entry_to_supabase(final_data):
    # Zapisuje pojedynczy wpis do bazy (łączy listy tagów)
    print(f"\nPrzetwarzanie: {final_data['name']}")

    try:
        # Sprawdzanie duplikatów filmów
        existing_check = supabase.table('films') \
            .select('id') \
            .eq('name', final_data['name']) \
            .eq('release_date', final_data['release_date']) \
            .execute()

        if existing_check.data and len(existing_check.data) > 0:
            print(f" DUPLIKAT FILMU: '{final_data['name']}' ({final_data['release_date']}) - Pomijam.")
            return 
        # ------------------------------------

        # 1. Dodaj Film do tabeli 'films'
        film_payload = {
            "name": final_data['name'],
            "release_date": final_data['release_date'],
            "director": final_data['director']
        }
        film_res = supabase.table('films').insert(film_payload).execute()
        
        # Pobranie ID nowo utworzonego filmu
        if hasattr(film_res, 'data') and len(film_res.data) > 0:
             film_id = film_res.data[0]['id']
        else:
             print("Błąd: Nie udało się pobrać ID filmu.")
             return

        print(f"Film dodany. ID: {film_id}")

        # 2. Łączenie wszystkich źródeł tagów (TMDB + AI + ewentualne legacy)
        tags_tmdb = final_data.get('tmdb_tags', [])
        tags_ai = final_data.get('ai_tags', [])
        tags_legacy = final_data.get('tags', [])
        
        # Łączymy listy i używamy set(), żeby usunąć ewentualne duplikaty między listami
        all_tags = list(set(tags_tmdb + tags_ai + tags_legacy))
        
        print(f"   Łącznie tagów: {len(all_tags)} (TMDB: {len(tags_tmdb)}, AI: {len(tags_ai)})")

        # 3. Zapis tagów
        for tag_name in all_tags:
            tag_name_clean = tag_name.strip().lower() 
            
            # Sprawdź czy tag istnieje
            existing_tag = supabase.table('tags').select('id').eq('tag_name', tag_name_clean).execute()
            
            if existing_tag.data:
                # Jeśli istnieje, pobierz jego ID
                tag_id = existing_tag.data[0]['id']
            else:
                # Jeśli nie istnieje, utwórz nowy i pobierz ID
                new_tag = supabase.table('tags').insert({"tag_name": tag_name_clean}).execute()
                tag_id = new_tag.data[0]['id']

            # 4. Relacja Many-to-Many
            try:
                supabase.table('films_tags').insert({
                    "film_id": film_id,
                    "tag_id": tag_id
                }).execute()
            except Exception:
                pass # Ignoruj błąd jeśli relacja już jest
                
        print(f"Sukces, zapisano.")
        
    except Exception as e:
        print(f"Błąd zapisu do bazy: {e}")

# --- GŁÓWNA LOGIKA ---
def main():
    # Konfiguracja parsera argumentów CLI
    parser = argparse.ArgumentParser(description="Automat do tagowania filmów")
    
    # Wymagane podanie jednej z dwóch opcji: --movies lub --save
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--movies', type=str, help='Lista filmów oddzielona średnikami')
    group.add_argument('--save', type=str, help='Ścieżka do pliku JSON z danymi do zapisania')

    args = parser.parse_args()

    # Tryb 1. Generowanie danych - pobieranie danych z TMDB i OPENAI API.
    if args.movies:
        movie_list = [m.strip() for m in args.movies.split(';') if m.strip()]
        results = []
        
        print(f"Rozpoczynam przetwarzanie {len(movie_list)} filmów")
        
        for movie_name in movie_list:
            tmdb_data = get_tmdb_data(movie_name)
            if tmdb_data:
                ai_result = get_ai_tags(tmdb_data)
                if ai_result:
                    results.append(ai_result)
        
        # Zapis wyników do pliku lokalnego w celu ręcznej weryfikacji
        filename = "output.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=4, ensure_ascii=False)
            
        print("\n" + "="*50)
        print(f"Zakończono. Wyniki w pliku: {filename}")
        print("="*50)

    # Tryb 2. Zapis do bazy danych Supabase (z pliku JSON)
    elif args.save:
        filename = args.save
        if not os.path.exists(filename):
            print(f"Plik {filename} nie istnieje!")
            return

        print(f"Wczytuję dane z {filename}...")
        with open(filename, 'r', encoding='utf-8') as f:
            try:
                data_to_save = json.load(f)
            except json.JSONDecodeError:
                print("Błąd: Plik niepoprawny.")
                return

        if not isinstance(data_to_save, list):
            print("Błąd: Oczekiwano listy w JSON.")
            return

        print(f"Rozpoczynam import {len(data_to_save)} filmów...")
        for entry in data_to_save:
            save_entry_to_supabase(entry)
        print("\nImport zakończony!")

if __name__ == "__main__":
    main()