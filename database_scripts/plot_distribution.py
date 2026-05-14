import os
import matplotlib.pyplot as plt
from collections import Counter
from supabase import create_client, Client
from dotenv import load_dotenv

# Skrypt pozwalający na zobrazowanie rozkładu wystąpień tagów w bazie danych.

# --- KONFIGURACJA SUPABASE ---
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") 

def fetch_all_tag_connections():
    # Pobiera wszystkie rekordy z tabeli films_Tags w paczkach. 
    print("Łączenie z Supabase...")
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Błąd konfiguracji klienta: {e}")
        return []

    all_tag_ids = []
    chunk_size = 1000
    offset = 0
    
    print("Pobieranie danych (może to chwilę potrwać)...")
    
    # Pętla - pobieramy dane kawałek po kawałku.
    while True:
        response = supabase.table('films_tags') \
            .select('tag_id') \
            .range(offset, offset + chunk_size - 1) \
            .execute()
        
        data = response.data
        
        # Jeśli brak danych, przerywamy pętlę
        if not data:
            break
        
        # Wyciągamy same ID z listy słowników [{'tag_id': 1}, {'tag_id': 5}...]
        batch_ids = [item['tag_id'] for item in data]
        all_tag_ids.extend(batch_ids)
        
        # Jeśli pobrano mniej niż limit, to znaczy, że to była ostatnia paczka
        if len(data) < chunk_size:
            break
            
        # Zliczamy wystąpienia każdego tagu.
        # Wynik: słownik {tag_id: liczba_wystąpień}
        offset += chunk_size
        print(f"Pobrano {offset} rekordów...")

    print(f"Zakończono pobieranie. Łącznie {len(all_tag_ids)} powiązań.")
    
    tag_counts = Counter(all_tag_ids)
    return list(tag_counts.values())

def plot_distribution(connections_list):
    # Rysuje histogram popularności tagów.
    if not connections_list:
        print("Brak danych do wyświetlenia.")
        return

    # Zliczamy rozkład
    distribution = Counter(connections_list)
    
    # Ustawiamy punkt odcięcia
    CUTOFF = 30
    
    # Przygotowujemy listy na dane do wykresu
    x_labels = []
    y_values = []
    
    # 1. Wypełniamy wartości od 1 do 30
    # Używamy range, żeby oś była ciągła (nie pomijała liczb, np. gdy nie ma tagów z 17 powiązaniami)
    for i in range(1, CUTOFF + 1):
        x_labels.append(str(i)) # Konwertujemy na string, bo to teraz etykiety
        y_values.append(distribution.get(i, 0)) # Pobierz wartość lub 0 jeśli brak
        
    # 2. Obliczamy sumę dla reszty (wszystkie tagi, które mają > 30 filmów)
    over_cutoff_count = sum(count for k, count in distribution.items() if k > CUTOFF)
    
    # 3. Dodajemy słupek zbiorczy
    x_labels.append(f">{CUTOFF}") # Etykieta ">30"
    y_values.append(over_cutoff_count)

    # Rysowanie
    plt.figure(figsize=(14, 7))
    
    # Rysujemy słupki
    bars = plt.bar(x_labels, y_values, color='#3ECF8E', edgecolor='#2A8F62')

    bars[-1].set_color('#2A8F62') 
    bars[-1].set_edgecolor('black')

    plt.title(f'Rozkład popularności tagów\n(Ostatni słupek sumuje wszystkie tagi powyżej {CUTOFF} powiązań)', fontsize=14)
    plt.xlabel('Liczba powiązań', fontsize=12)
    plt.ylabel('Liczba tagów (sztuk)', fontsize=12)
    
    # Siatka
    plt.grid(axis='y', linestyle='--', alpha=0.3)

    # Wartości nad słupkami
    for bar in bars:
        height = bar.get_height()
        # Wyświetlamy liczbę tylko jeśli jest większa od 0, żeby nie śmiecić wykresu
        if height > 0:
            plt.text(bar.get_x() + bar.get_width()/2., height,
                     f'{int(height)}',
                     ha='center', va='bottom', fontsize=9, rotation=0)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    connections_data = fetch_all_tag_connections()
    plot_distribution(connections_data)