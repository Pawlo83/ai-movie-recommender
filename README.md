<details open>
<a name="polish-version"></a>
<summary><strong>🇵🇱 Polski</strong> &nbsp;|&nbsp; <a href="#english-version">🇬🇧 English below</a></summary>

# System rekomendacji filmowych oparty na AI

![Project Status](https://img.shields.io/badge/status-on_hold-blue)
![Backend](https://img.shields.io/badge/backend-Python_3.12-blue)
![Frontend](https://img.shields.io/badge/frontend-Angular_20-blue)
![Database](https://img.shields.io/badge/database-Supabase-blue)
![License](https://img.shields.io/badge/license-MIT-blue)

Znalezienie odpowiedniego filmu nie powinno zajmować więcej czasu niż sam seans. **MovieTell** pozwala opisać swój nastrój w dowolny sposób - tagami z wagami, swobodnym tekstem lub obydwoma naraz. Zwraca 10 dopasowanych produkcji wraz z plakatami, dostępnością na platformach streamingowych oraz wytłumaczeniem, dlaczego każdy film trafił na listę.

![GIF](MovieTell.gif)

## Kluczowe funkcjonalności
* **Silnik NLP:** SpaCy analizuje drzewo zależności składniowych, wykrywa negacje i lematyzuje tekst; `sentence-transformers` mapuje wyniki na tagi bazy danych przez podobieństwo cosinusowe.
* **Inteligentna pre-agregacja SQL:** Algorytm AND→OR iteracyjnie rozszerza zbiór tagów aż do osiągnięcia puli 50–150 filmów, minimalizując ryzyko pustego kontekstu dla modelu AI.
* **Weryfikacja przez TMDB:** każda propozycja AI jest sprawdzana w The Movie Database zanim trafi do użytkownika, a nieistniejące filmy są odrzucane.
* **Automatyczne tagowanie w tle:** Nowe filmy wygenerowane przez AI są asynchronicznie tagowane przez LLM i dodawane do bazy bez blokowania odpowiedzi API.
* **Inteligentny cache:** Identyczne zapytania są obsługiwane bezpośrednio z tabeli `gpt_response` w Supabase, bez kosztownych wywołań LLM.
* **Panel administratora:** Zarządzanie filmami, tagami i powiązaniami jest dostępne z aplikacji webowej, został on zabezpieczony JWT z mechanizmem heartbeat co 30 sekund.

## Architektura i technologie
System oparty jest na architekturze trójwarstwowej klient-serwer. Komunikacja między warstwami odbywa się bezstanowo przez HTTP/HTTPS z wymianą danych w formacie JSON.

### Silnik rekomendacji i NLP
* **Język:** Python 3.12
* **Framework:** Django 5.2 & Gunicorn
* **REST API:** Centralny węzeł sterujący, odpowiedzialny za logikę biznesową, autoryzację oraz komunikację z modelami sztucznej inteligencji.
* **Przetwarzanie NLP:** Zaawansowany potok analityczny wykorzystujący m.in. biblioteki SpaCy oraz SentenceTransformers.

### Baza danych
* **Platforma:** Supabase (PostgreSQL)
* **Logika po stronie serwera:** Wykorzystanie wbudowanych funkcji RPC (Remote Procedure Calls) do odciążenia backendu i wykonywania złożonych operacji filtrowania oraz pre-agregacji bezpośrednio w warstwie bazy danych.
* **Źródła danych:** Początkowe zasilenie systemu oparto na rankingu 1000 najbardziej dochodowych produkcji z Box Office Mojo. Twarde metadane pobrano przy pomocy TMDB API, a następnie wzbogacono je o etykiety wygenerowane przez modele uczenia maszynowego, które następnie manualnie weryfikowano i optymalizowano.

### Aplikacja webowa
* **Język:** TypeScript
* **Framework:** Angular 20
* **Interfejs użytkownika:** Reaktywna aplikacja SPA, która w jednym formularzu umożliwia wprowadzanie zapytań w języku naturalnym, jak i użycie dynamicznie autouzupełnianych etykiet wraz z wagami.
* **Panel administracyjny (CRUD):** Zabezpieczony mechanizmem JWT moduł zarządzania bazą wiedzy. Wykorzystuje generyczne tabele (dynamicznie budowane na podstawie struktury odpowiedzi JSON z API) oraz inteligentny system detekcji zmian w formularzach, który wysyła do serwera tylko zmodyfikowane pola w celu minimalizacji obciążenia sieci.

## Przetwarzanie języka naturalnego
Użytkownik może wpisać dowolny opis po angielsku, a algorytm przetwarza go w czterech warstwach:

**1. Inicjalizacja (singleton, lazy loading)**

Modele neuronowe spaCy i SentenceTransformer są ładowane do pamięci raz przy pierwszym zapytaniu i trzymane przez cały czas życia procesu. Wektory wszystkich tagów z bazy danych są przeliczane przy starcie i cachowane jako tensory, żeby każde kolejne zapytanie nie musiało przeliczać ich od nowa.

**2. Ekstrakcja morfosyntaktyczna (spaCy)**

Tekst trafia do modelu spaCy `en_core_web_sm`, który buduje drzewo zależności składniowych. Algorytm odrzuca interpunkcję, liczby, stop words i przepuszcza tylko rzeczowniki, przymiotniki, czasowniki i nazwy własne (POS tagging). Wieloczłonowe nazwy własne są scalane w jeden token przed analizą (np. `Christopher Nolan` to jeden węzeł). Każdy z tokenów jest lematyzowany do formy podstawowej.

**3. Analiza kontekstu i wag (Linear Lookback)**

Dla każdego tokenu funkcja `analyze_syntax_modifiers()` sprawdza jego otoczenie w dwóch krokach: najpierw przeszukuje bezpośrednich potomków węzła w drzewie zależności, potem cofa się liniowo o maksymalnie 4 tokeny wstecz w oryginalnym tekście. Jeśli w otoczeniu pojawi się negacja (`not`, `without`, `never`) token jest flagowany jako wykluczony i otrzymuje wagę `-1.0` w słowniku wyników. Jeśli pojawi się modyfikator intensywności (`very`, `slightly`, `extremely`) waga tokena jest korygowana o jego wartość ze słownika. Intensyfikatory drugiego rzędu są obsługiwane przez analizę dzieci modyfikatora z dodatkową korektą ±0.2.

Wynikiem działania tego etapu jest słownik, w którym kluczem jest lemat wyrazu, a wartością lista przypisanych mu wag. Agregacja w formie listy jest kluczowa, ponieważ to samo słowo mogło wystąpić w tekście wielokrotnie w różnym kontekście. Wartości ujemne oznaczają twarde wykluczenia, a dodatnie preferencje użytkownika.

**4. Wektoryzacja i decyzja końcowa (SentenceTransformer)**

Lematy są enkodowane przez model `all-MiniLM-L6-v2` do 384-wymiarowych embeddingów. Następnie liczone jest podobieństwo cosinusowe między każdym lematem a wszystkimi tagami z bazy danych. Dopasowanie jest uznawane za pewne przy progu ≥ 0.75 (wartość dobrana eksperymentalnie). Wagi z etapu 3 są agregowane per tag i konwertowane na skalę 1–7 gwiazdek przez funkcję `calculate_stars()`, z bonusem za wielokrotne wystąpienia tego samego tagu w opisie.

Zmapowane kryteria rozchodzą się następnie w dwóch kierunkach jednocześnie: tagi z `rating > 0` trafiają do pre-agregacji SQL i służą do wybrania puli 50-150 filmów z bazy jako kontekst dla modelu, natomiast pełna lista kryteriów trafia bezpośrednio do modelu AI jako osobne pole. Model traktuje tagi z wagą `-1` jako twarde zakazy: żaden film posiadający zakazany tag nie może znaleźć się w wynikach, a filmy syntetyzowane spoza bazy nie mogą posiadać cech nim określonych.

Cały proces jest bezstanowy - nie korzysta z historii oglądania ani profilu użytkownika. Wynik zależy wyłącznie od bieżącego zapytania.

## Instalacja i uruchomienie

### Wymagania wstępne
* Python 3.12+
* Node.js 20+ oraz Angular CLI (`npm install -g @angular/cli`)
* Konto Supabase z wypełnionym schematem (skrypt: `database_scripts/schema.sql`)
* Klucz OpenAI API
* Klucz TMDB API

### Backend

```bash
cd backend
pip install -r requirements.txt
```

Utwórz plik `.env` w katalogu `backend/` i uzupełnij zmienne:

| Zmienna | Opis |
|---|---|
| `DJANGO_KEY` | Tajny klucz Django |
| `APP_LOGIN_USERNAME` | Login do panelu administratora |
| `APP_LOGIN_PASSWORD` | Hasło do panelu administratora |
| `ALLOWED_HOSTS` | Dozwolone hosty oddzielone przecinkami (np. `localhost,127.0.0.1`) |
| `CSRF_TRUSTED_ORIGINS` | Adres frontendu (np. `http://localhost:4200`) |
| `CORS_ALLOWED_ORIGINS` | Adres frontendu (np. `http://localhost:4200`) |
| `SUPABASE_URL` | URL projektu Supabase |
| `SUPABASE_KEY` | Klucz Supabase |
| `OPENAI_API_KEY` | Klucz OpenAI API |
| `TMDB_API_KEY` | Klucz TMDB API |

```bash
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
ng serve
```

Aplikacja dostępna pod adresem `http://localhost:4200`.

## Autorzy
Projekt wykonany został w ramach pracy inżynierskiej na Politechnice Poznańskiej w 2026 roku, promotorem był dr Paweł Misiorek.
* [Aleksander Klemm](https://github.com/Alex911KL)
* [Kacper Molenda](https://github.com/caprimol)
* [Paweł Skiba](https://github.com/Pawlo83)
* [Maciej Stypułkowski](https://github.com/stypekmaslo6)

</details>

---

<a name="english-version"></a>
<details>
<summary><strong>🇬🇧 English</strong> &nbsp;|&nbsp; <a href="#polish-version">🇵🇱 Polski above</a></summary>

# AI-powered Movie Recommendation System

![Project Status](https://img.shields.io/badge/status-on_hold-blue)
![Backend](https://img.shields.io/badge/backend-Python_3.12-blue)
![Frontend](https://img.shields.io/badge/frontend-Angular_20-blue)
![Database](https://img.shields.io/badge/database-Supabase-blue)
![License](https://img.shields.io/badge/license-MIT-blue)

Finding the right movie shouldn't take longer than watching one. **MovieTell** lets you describe your mood however you like - weighted tags, free-text, or both. It returns 10 curated films with posters, streaming availability, and an explanation of why each one made the list.

![GIF](MovieTell.gif)

## Key features
* **NLP engine:** spaCy parses dependency trees, detects negations and lemmatizes text; `sentence-transformers` maps results to database tags via cosine similarity.
* **Smart SQL pre-aggregation:** An AND→OR algorithm iteratively expands the tag set until a pool of 50–150 films is reached, minimizing the risk of empty context for the AI model.
* **TMDB verification:** Every AI suggestion is verified against The Movie Database before being returned to the user; non-existent films are dropped.
* **Async auto-tagging:** New films generated by the AI are asynchronously tagged by the LLM and added to the database without blocking the API response.
* **Intelligent cache:** Identical queries are served directly from the `gpt_response` table in Supabase, avoiding costly LLM calls.
* **Admin panel:** Film, tag and association management is available directly from the web app, secured with JWT and a 30-second heartbeat mechanism.

## Architecture and technologies
The system is built on a three-tier client-server architecture. Communication between layers is stateless over HTTP/HTTPS with JSON as the data exchange format.

### Recommendation and NLP engine
* **Language:** Python 3.12
* **Framework:** Django 5.2 & Gunicorn
* **REST API:** The central control node, responsible for business logic, authorization and communication with AI models.
* **NLP processing:** An advanced analytics pipeline using spaCy and SentenceTransformers among other libraries.

### Database
* **Platform:** Supabase (PostgreSQL)
* **Server-side logic:** Built-in RPC (Remote Procedure Calls) functions offload the backend and execute complex filtering and pre-aggregation operations directly at the database layer.
* **Data sources:** The initial dataset is based on the Top 1000 all-time grossing films from Box Office Mojo. Hard metadata was fetched via the TMDB API and then enriched with tags generated by machine learning models, which were subsequently manually verified and optimized.

### Web application
* **Language:** TypeScript
* **Framework:** Angular 20
* **UI:** A reactive SPA that combines natural language input with dynamically autocompleted weighted tags in a single form.
* **Admin panel (CRUD):** A JWT-secured knowledge base management module. Uses generic tables dynamically built from the JSON structure returned by the API, and an intelligent change-detection system that sends only modified fields to the server to minimize network overhead.

## Natural language processing
The user can type any description in English and the algorithm processes it in four layers:

**1. Initialization (singleton, lazy loading)**

The spaCy and SentenceTransformer neural models are loaded into memory once on the first request and kept alive for the lifetime of the process. Vectors for all database tags are computed at startup and cached as tensors, so subsequent requests never recompute them.

**2. Morphosyntactic extraction (spaCy)**

The text is passed to the spaCy model `en_core_web_sm`, which builds a dependency parse tree. The algorithm discards punctuation, numbers and stop words, and passes through only nouns, adjectives, verbs and proper nouns (POS tagging). Multi-word proper nouns are merged into a single token before analysis (e.g. `Christopher Nolan` is one node). Each token is lemmatized to its base form.

**3. Context and weight analysis (Linear Lookback)**

For each token, `analyze_syntax_modifiers()` inspects its surroundings in two steps: first it searches the direct children of the node in the dependency tree, then it steps back linearly up to 4 tokens in the original text. If a negation appears nearby (`not`, `without`, `never`), the token is flagged as excluded and receives a weight of `-1.0` in the results dictionary. If an intensity modifier appears (`very`, `slightly`, `extremely`), the token's weight is adjusted by its dictionary value. Second-order intensifiers are handled by inspecting the modifier's own children with an additional ±0.2 correction.

The output of this stage is a dictionary where the key is the lemma and the value is a list of weights assigned to it. Aggregation as a list is essential because the same word may have appeared multiple times in the text in different contexts. Negative values represent hard exclusions, positive values represent user preferences.

**4. Vectorization and final decision (SentenceTransformer)**

Lemmas are encoded by `all-MiniLM-L6-v2` into 384-dimensional embeddings. Cosine similarity is then computed between each lemma and every tag in the database. A match is considered confident at threshold ≥ 0.75 — determined experimentally. Weights from step 3 are aggregated per tag and converted to a 1–7 star scale by `calculate_stars()`, with a bonus for repeated occurrences of the same tag in the description.

The mapped criteria then split into two paths simultaneously: tags with `rating > 0` go to the SQL pre-aggregation step and are used to select a pool of 50–150 films from the database as context for the model, while the full criteria list is sent directly to the AI model as a separate field. The model treats tags with weight `-1` as hard bans: no film carrying a banned tag can appear in the results, and synthesized films generated outside the database cannot possess characteristics defined by that tag.

The entire process is stateless — it uses no watch history or user profile. The result depends solely on the current query.

## Setup

### Prerequisites
* Python 3.12+
* Node.js 20+ and Angular CLI (`npm install -g @angular/cli`)
* A Supabase account with the schema applied (`database_scripts/schema.sql`)
* OpenAI API key
* TMDB API key

### Backend

```bash
cd backend
pip install -r requirements.txt
```

Create a `.env` file inside `backend/` and fill in the following variables:

| Variable | Description |
|---|---|
| `DJANGO_KEY` | Django secret key |
| `APP_LOGIN_USERNAME` | Admin panel login |
| `APP_LOGIN_PASSWORD` | Admin panel password |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts (e.g. `localhost,127.0.0.1`) |
| `CSRF_TRUSTED_ORIGINS` | Frontend origin (e.g. `http://localhost:4200`) |
| `CORS_ALLOWED_ORIGINS` | Frontend origin (e.g. `http://localhost:4200`) |
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_KEY` | Supabase key |
| `OPENAI_API_KEY` | OpenAI API key |
| `TMDB_API_KEY` | TMDB API key |

```bash
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
ng serve
```

App available at `http://localhost:4200`.

## Authors
This project was developed as an engineering thesis at Poznań University of Technology in 2026, supervised by dr Paweł Misiorek.
* [Aleksander Klemm](https://github.com/Alex911KL)
* [Kacper Molenda](https://github.com/caprimol)
* [Paweł Skiba](https://github.com/Pawlo83)
* [Maciej Stypułkowski](https://github.com/stypekmaslo6)

</details>