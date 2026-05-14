import sys
from supabase import create_client, Client
import os
import json
from dotenv import load_dotenv

# Skrypt pomocniczy do skryptu postprocess_long_tags, który pozwala sprawnie "wymienić" stare tagi na parę nowych 
# lub całkowicie go usunąć gdy wydaje się bezużyteczny.

# --- KONFIGURACJA ---
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") 

# Inicjalizacja klientów
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def execute_split(PLAN_PODZIALU):
    # Funkcja iteruje po słowniku zmian i wykonuje operacje na bazie danych.
    """
    Schemat: 
    1. Znajdź stary tag.
    2. Pobierz jego filmy.
    3. Przypisz te filmy do nowych tagów.
    4. Usuń stary tag.
    """
    print(f"Rozpoczynam podział {len(PLAN_PODZIALU)} tagów")
    
    for old_name, new_parts in PLAN_PODZIALU.items():
        # Pomijamy, jeśli nie ma zmian
        if len(new_parts) == 1 and new_parts[0].lower() == old_name.lower():
            continue

        print(f"\n Przetwarzam: '{old_name}' -> {new_parts}")

        # 1. Znajdź ID starego taga
        res = supabase.table('tags').select('id').eq('tag_name', old_name).execute()
        if not res.data:
            print(f"Tag źródłowy '{old_name}' nie istnieje już w bazie. Pomijam.")
            continue
        
        old_id = res.data[0]['id']

        # 2. Pobierz filmy przypisane do starego taga
        links = supabase.table('films_tags').select('film_id').eq('tag_id', old_id).execute().data
        if not links:
            print("Brak filmów dla tego taga.")
            # I tak usuwamy pusty tag
            supabase.table('tags').delete().eq('id', old_id).execute()
            continue

        print(f"Aktualizuję {len(links)} filmów")

        # 3. Pętla po nowych składnikach (tworzenie nowych relacji)
        for part in new_parts:
            part_clean = part.strip().lower()
            
            # Znajdź lub stwórz nowy tag
            tag_res = supabase.table('tags').select('id').eq('tag_name', part_clean).execute()
            if tag_res.data:
                new_tag_id = tag_res.data[0]['id']
            else:
                # Jeśli nie istnieje, tworzymy go
                new_tag = supabase.table('tags').insert({'tag_name': part_clean}).execute()
                new_tag_id = new_tag.data[0]['id']
            
            # Przypisz filmy
            for link in links:
                try:
                    supabase.table('films_tags').insert({
                        'film_id': link['film_id'],
                        'tag_id': new_tag_id
                    }).execute()
                except Exception:
                    pass # Ignoruj, jeśli film już miał ten nowy tag

        # 4. Na koniec usuń stary tag i jego relacje
        supabase.table('films_tags').delete().eq('tag_id', old_id).execute()
        supabase.table('tags').delete().eq('id', old_id).execute()
        print("   Gotowe.")

if __name__ == "__main__":
    # Nazwa pliku wygenerowanego przez poprzedni skrypt (postprocess_long_tags)
    filename = "plan_skracania.json"

    # Sprawdź czy plik istnieje
    if not os.path.exists(filename):
        print(f"Błąd: Nie znaleziono pliku '{filename}'. Uruchom najpierw skrypt generujący plan.")
    else:
        # Wczytaj plik JSON
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                loaded_plan = json.load(f)
            
            if not loaded_plan:
                print(f"Plik '{filename}' jest pusty lub zawiera puste dane.")
            else:
                execute_split(loaded_plan)
                
        except json.JSONDecodeError:
            print(f"Błąd: Plik '{filename}' nie zawiera poprawnego formatu JSON.")