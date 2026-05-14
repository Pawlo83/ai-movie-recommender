import json
import time
from supabase import create_client, Client
from openai import OpenAI
import os
import argparse
from dotenv import load_dotenv

# Skrypt używany do filtracji bazy danych - znajduje wszystkie rekordy ze słówkiem kluczowym i "rozbija" złożone tagi na oddzielne wyrazy
# Pozwala to odflitrować niepotrzebne tagi wygenerowane przez AI, które brzmią bardzo podobnie a mają ten sam sens.

# --- KONFIGURACJA ---
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") 
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Inicjalizacja klientów
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
client_ai = OpenAI(api_key=OPENAI_API_KEY)

def fetch_long_tags(keyword):
    # Pobiera z bazy wszystkie tagi zawierające podane słowo kluczowe.
    print("Pobieram tagi z bazy")
    
    # Zapytanie ILIKE %keyword%
    response = supabase.table('tags') \
        .select('tag_name') \
        .ilike('tag_name', f'%{keyword}%') \
        .execute()
    
    # Tutaj response.data zawiera już tylko przefiltrowane wyniki
    matched_tags = [t['tag_name'] for t in response.data]
            
    return matched_tags

def get_short_names_batch(tags_list, keyword):
    # Wysyła paczkę tagów do modelu AI w celu ich przeanalizowania i rozbicia.
    # Zwraca słownik: {"stara_nazwa": ["człon1", "człon2"]}

    prompt = f"""
    Jesteś analitykiem bazy danych. Masz listę tagów, które zawierają wspólne słowo kluczowe: "{keyword}".
    
    ZADANIE:
    Twoim celem jest "atomizacja" tych tagów. Rozdziel każdy złożony tag na:
    1. Słowo kluczowe ("{keyword}").
    2. Drugi człon (to co zostaje po odjęciu słowa kluczowego).

    ZASADY:
    1. Format wyjściowy to JSON.
    2. Przykład: "animal attack" -> "{keyword}", "attack"
    3. Przykład: "wild {keyword}" -> "wild", "{keyword}"
    4. Przykład: "{keyword} rescue" -> "{keyword}", "rescue"
    5. Jeśli tag po usunięciu słowa kluczowego staje się bezsensowny (śmieć/opis fabuły) -> Zwróć pustą listę [] (oznacza usunięcie).
    6. Jeśli tag to TYLKO samo słowo "{keyword}" -> Zwróć "{keyword}" (bez zmian).

    Wymagany format JSON:
    {{
       "stary tag 1": ["słowo_wspólne", "reszta"],
       "stary tag 2": ["słowo_wspólne", "reszta"],
       "tag do usuniecia": []
    }}
    
    Lista do przetworzenia:
    {json.dumps(tags_list, ensure_ascii=False)}
    """

    try:
        # Wywołanie API OpenAI
        response = client_ai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={ "type": "json_object" } # Wymuszenie poprawnego JSON-a
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Błąd AI: {e}")
        return {}

def main():
    # Definiujemy parser argumentów
    parser = argparse.ArgumentParser(description="Skrypt do atomizacji tagów przy użyciu AI.")
    parser.add_argument('keyword', type=str, help='Słowo kluczowe, dla którego szukamy złożonych tagów (np. "century", "war")')
    parser.add_argument('--output', type=str, default="plan_skracania.json", help='Nazwa pliku wynikowego JSON')
    args = parser.parse_args()

    keyword = args.keyword
    output_filename = args.output

    # Pobranie kandydatów do obróbki
    candidates = fetch_long_tags(keyword)
    print(f"Znaleziono {len(candidates)} tagów do analizy.")
    
    full_plan = {}
    BATCH_SIZE = 20
    
    # Pętla przetwarzania
    for i in range(0, len(candidates), BATCH_SIZE):
        batch = candidates[i : i + BATCH_SIZE]
        print(f"Analizuję paczkę {i+1}-{min(i+BATCH_SIZE, len(candidates))}...")
        
        # Pobieramy mapowanie: {"stary": "nowy"}
        result = get_short_names_batch(batch, keyword)
        
        for old, new_parts in result.items():
            
            # Wariant A: AI zwróciło listę
            if isinstance(new_parts, list):
                # Czyścimy każdy element listy (małe litery, usuwanie spacji)
                cleaned_parts = [part.strip().lower() for part in new_parts if part and part.strip()]
                full_plan[old] = cleaned_parts

            # Wariant B: AI się pomyliło i zwróciło stringa
            elif isinstance(new_parts, str):
                if new_parts.strip():
                    full_plan[old] = [new_parts.strip().lower()]
                else:
                    full_plan[old] = []
            
            # Wariant C: Puste/Null
            else:
                full_plan[old] = []


    # Zapis do pliku
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(full_plan, f, indent=4, ensure_ascii=False)

    print(f"\nGotowe. Wynik zapisano w pliku '{output_filename}'.")
    print("Otwórz go, zweryfikuj, a potem uruchom program split_tags.py")

if __name__ == "__main__":
    main()