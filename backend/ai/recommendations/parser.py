import json
from openai.types.chat.chat_completion import ChatCompletion

def extract_recommendations(completion: ChatCompletion) -> list[dict]:
    """
    Odpowiada za wydobycie i podstawową walidację danych zwróconych przez model
    w ramach mechanizmu function calling.

    Funkcja:
    - odczytuje `function_call.arguments` z odpowiedzi modelu,
    - parsuje wynik do struktury Python (dict / list),
    - weryfikuje obecność pola `recommendations`.

    Moduł ten pełni wyłącznie rolę warstwy pośredniej między API OpenAI
    a dalszym przetwarzaniem wyników.
    """
    choice = completion.choices[0].message
    fc = getattr(choice, "function_call", None)

    if not fc or not getattr(fc, "arguments", None):
        raise ValueError("Brak function_call.arguments")

    args = json.loads(fc.arguments) if isinstance(fc.arguments, str) else fc.arguments

    if not isinstance(args, dict) or "recommendations" not in args:
        raise ValueError("Nieprawidłowy format odpowiedzi")

    if not isinstance(args["recommendations"], list):
        raise ValueError("Pole recommendations nie jest listą")

    return args["recommendations"]