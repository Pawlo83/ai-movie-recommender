import json
from openai.types.chat.chat_completion import ChatCompletion


def extract_function_arguments(completion: ChatCompletion) -> dict:
    """
    Wydobywa i parsuje argumenty wywołania narzędzia (tool calling) z odpowiedzi modelu.

    Obsługuje zarówno nowy format `tool_calls`, jak i starszy `function_call`,
    dzięki czemu działa z OpenAI oraz z bramkami zgodnymi z OpenAI Chat Completions.
    """
    message = completion.choices[0].message

    tool_calls = getattr(message, "tool_calls", None)
    if tool_calls:
        raw_arguments = tool_calls[0].function.arguments
    else:
        function_call = getattr(message, "function_call", None)
        if not function_call or not getattr(function_call, "arguments", None):
            raise ValueError("Brak tool_calls/function_call w odpowiedzi modelu")
        raw_arguments = function_call.arguments

    args = (
        json.loads(raw_arguments)
        if isinstance(raw_arguments, str)
        else raw_arguments
    )

    if not isinstance(args, dict):
        raise ValueError("Nieprawidłowy format argumentów odpowiedzi")

    return args


def extract_recommendations(completion: ChatCompletion) -> list[dict]:
    """
    Odpowiada za wydobycie i podstawową walidację danych zwróconych przez model
    w ramach mechanizmu tool calling.

    Funkcja:
    - odczytuje argumenty wywołania narzędzia z odpowiedzi modelu,
    - parsuje wynik do struktury Python (dict / list),
    - weryfikuje obecność pola `recommendations`.

    Moduł ten pełni wyłącznie rolę warstwy pośredniej między API modelu
    a dalszym przetwarzaniem wyników.
    """
    args = extract_function_arguments(completion)

    if "recommendations" not in args:
        raise ValueError("Nieprawidłowy format odpowiedzi")

    if not isinstance(args["recommendations"], list):
        raise ValueError("Pole recommendations nie jest listą")

    return args["recommendations"]
