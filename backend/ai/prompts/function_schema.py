def build_functions_schema() -> list[dict]:
    """
    Definiuje schemat wywołania funkcji (function calling) wykorzystywany przez model OpenAI
    do zwracania rekomendacji filmowych w ściśle ustrukturyzowanym formacie JSON.

    Schemat wymusza:
    - Użycie jednej, konkretnej funkcji (`generate_recommendations`) jako jedynej
      dopuszczalnej formy odpowiedzi modelu.
    - Strukturę danych, możliwą do bezpiecznego parsowania.
    - Jawne typy dla każdego pola rekomendacji.

    Kluczowe założenia:
    - Model ZAWSZE zwraca jeden obiekt najwyższego poziomu zawierający tablicę
      `recommendations`.
    - Każdy element tablicy reprezentuje jedną rekomendację filmu, pochodzącą
      albo z wewnętrznej bazy danych (`synthesis = false`), albo zaproponowaną
      przez model spoza bazy (`synthesis = true`).
    - Pola identyfikacyjne (`candidate_tmdb_id`, `candidate_release_date`)
      mogą przyjmować wartość null, jeżeli nie są jednoznacznie znane, jednak
      ich status weryfikacji MUSI zostać zawsze określony.
    - Pole `confidence` jest znormalizowanym wynikiem dopasowania (zakres 0.0–1.0),
      wykorzystywanym do rankingu i dalszego przetwarzania, a nie bezpośredniej
      prezentacji użytkownikowi.
    - Pole `selection_reason` jest obowiązkowe i zawiera zwięzłe, merytoryczne
      uzasadnienie wyboru filmu w kontekście kryteriów użytkownika.
    """
    return [
        {
            "name": "generate_recommendations",
            "parameters": {
                "type": "object",
                "properties": {
                    "recommendations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "candidate_tmdb_id": {"type": ["integer", "null"]},
                                "candidate_release_date": {"type": ["string", "null"]},
                                "tmdb_id_verification": {"type": "string", "enum": ["exact","approximate","unknown"]},
                                "release_date_verification": {"type": "string", "enum": ["exact","approximate","unknown"]},
                                "overview": {"type": ["string","null"]},
                                "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                                "synthesis": {"type": "boolean"},
                                "selection_reason": {"type": ["string","null"]}
                            },
                            "required": ["title","candidate_tmdb_id","candidate_release_date","tmdb_id_verification","release_date_verification","overview","confidence","synthesis","selection_reason"]
                        }
                    }
                },
                "required": ["recommendations"]
            }
        }
    ]