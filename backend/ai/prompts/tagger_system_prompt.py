def build_tagging_system_prompt() -> dict:
    """
    Buduje systemowy prompt dla modelu tagującego filmy.

    Prompt wymusza przypisanie tagów wyłącznie z dostarczonego słownika
    oraz zwrócenie wyniku w postaci JSON poprzez function calling,
    co zapewnia spójność danych.
    """
    return {
        "role": "system",
        "content": (
            "Jesteś silnikiem tagowania filmów.\n"
            "Twoim zadaniem jest przypisać KAŻDEMU filmowi listę tagów.\n\n"
            "DOSTĘPNE tagi pochodzą WYŁĄCZNIE z przekazanego słownika.\n"
            "Nie wolno tworzyć nowych tagów.\n"
            "Nie wolno zmieniać pisowni.\n\n"
            "Musisz zwrócić WYŁĄCZNIE JSON przez function calling."
        )
    }