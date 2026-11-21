def build_tagging_function_schema() -> list[dict]:
    """
    Definiuje schemat narzędzia (tool calling) wykorzystywany przez model OpenAI
    do zwracania przypisania tagów do filmów wygenerowanych przez AI
    w ściśle ustrukturyzowanym formacie JSON.

    Schemat wymusza:
    - Użycie jednej, konkretnej funkcji (`assign_tags`) jako jedynej
      dopuszczalnej formy odpowiedzi modelu.
    - Strukturę danych, możliwą do bezpiecznego parsowania.
    - Jawne typy dla każdego pola rekomendacji.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "assign_tags",
                "description": "Przypisuje listę tagów do każdego filmu",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "movies": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "tmdb_id": {"type": "number"},
                                    "tags": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                },
                                "required": ["tmdb_id", "tags"]
                            }
                        }
                    },
                    "required": ["movies"]
                }
            }
        }
    ]
