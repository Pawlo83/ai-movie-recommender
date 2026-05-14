def build_message_prompt(criterions: list[dict]) -> dict:
    """
    Buduje właściwą wiadomość przekazywaną do modelu,
    zawierającą konkretne kryteria wyboru rekomendacji.

    Prompt:
    - przekazuje modelowi listę kryteriów wraz z ich wagami,
    - inicjuje proces generowania rekomendacji dla danego zestawu preferencji,
    - stanowi punkt wejścia dla logiki zdefiniowanej w system prompt
      oraz instruction prompt.

    Funkcja nie zawiera logiki decyzyjnej — odpowiada wyłącznie
    za sformatowanie danych wejściowych do modelu.
    """
    return {
        "role": "user",
        "content": (
            "Zaproponuj DOKŁADNIE 10 rekomendacji filmowych "
            "najlepiej dopasowanych do następujących kryteriów użytkownika:\n\n"
            f"{criterions}\n\n"
            "Uwzględnij dane z 'database_movies' zgodnie z przekazanymi zasadami. "
            "Odpowiedz WYŁĄCZNIE poprzez wywołanie funkcji 'generate_recommendations'."
        )
    }