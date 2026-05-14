def build_instruction_prompt(movies_from_db: list, criterions: list[dict]) -> dict:
    """
    Buduje prompt instrukcji opisujący algorytm wyboru
    i rankingu rekomendacji filmowych.

    Instrukcja:
    - definiuje kolejne etapy przetwarzania (wykluczenia, filtr główny, ranking ważony, eksploracja),
    - precyzuje sposób interpretacji wag kryteriów użytkownika (w tym wag ujemnych),
    - określa twarde ograniczenia dotyczące liczby i jakości rekomendacji,
    - uzupełnia zasady systemowe o reguły selekcji i fallbacków.

    Prompt ten odpowiada za część logiki rekomendacji
    i działa komplementarnie do system promptu.
    """
    return {
            "database_movies": movies_from_db,
            "criterions": criterions,
            "instructions": (
                "Zachowanie rekomendacji przebiega w czterech kluczowych etapach:\n\n"

                "ETAP 0 – FILTR BEZWZGLĘDNYCH WYKLUCZEŃ (ZAKAZY):\n"
                "- Sprawdź, czy na liście kryteriów znajduje się tag z wartością `rating: -1`.\n"
                "- Waga -1 to TWARDY ZAKAZ (użytkownik kategorycznie NIE CHCE takich treści).\n"
                "- MUSISZ NATYCHMIAST odrzucić każdy film, który posiada ten tag, "
                "nawet jeśli idealnie pasuje do pozostałych kryteriów.\n"
                "- Nigdy nie generuj nowych filmów (synthesized: True), które posiadają cechy "
                "określone tagiem z wagą -1.\n\n"

                "ETAP 1 – FILTR GŁÓWNY:\n"
                "- Zidentyfikuj kryterium (lub kryteria) o NAJWYŻSZEJ wadze.\n"
                "- TYLKO filmy pasujące do tych kryteriów mogą stanowić podstawę rekomendacji.\n\n"
                "- Filmy spoza 'database_movies' MOGĄ przejść filtr główny, "
                "jeśli spełniają kryteria o najwyższych wagach i nie łamią ZAKAZÓW z Etapu 0.\n\n"

                "ETAP 2 – RANKING WAŻONY:\n"
                "- Dla każdego filmu oblicz wynik jako SUMĘ wag kryteriów, które spełnia.\n"
                "- Dopasowanie semantyczne jest DOZWOLONE wyłącznie dla kryteriów o "
                "najwyższej wadze.\n"
                "- Kryteria o niższej wadze (dodatniej) działają jako BONUS i mogą jedynie zwiększać "
                "pozycję filmu w rankingu, nigdy jej nie definiować.\n"
                "- Pochodzenie filmu (baza vs spoza bazy) NIE jest czynnikiem rankingowym.\n"
                "- Ranking opiera się WYŁĄCZNIE na ważonym dopasowaniu do kryteriów.\n"


                "ETAP 3 – EKSPLORACJA KONTROLOWANA:\n"
                "- Jeżeli po etapie 1 i 2 istnieją filmy spoza 'database_movies', "
                "które lepiej spełniają kryteria o najwyższej wadze niż filmy z bazy:\n"
                "- TAKIE filmy POWINNY być preferowane, nawet jeśli w bazie "
                "istnieją słabiej dopasowane rekordy.\n"
                "- Jeżeli filmy spoza 'database_movies' oferują "
                "ISTOTNIE LEPSZE połączenie WIELU kryteriów o wysokiej wadze "
                "(szczególnie w przypadku kryteriów klimatycznych), "
                "POWINNY one zastąpić słabsze filmy z bazy, "
                "nawet jeśli baza zawiera wystarczającą liczbę rekomendacji.\n"

                "UWAGA:\n"
                "- Jeżeli WIĘCEJ NIŻ JEDNO kryterium ma wagę ≥5,\n"
                "  film spełniający WYŁĄCZNIE jedno z nich\n"
                "  NIE jest uznawany za wystarczająco dopasowany,\n"
                "  nawet jeśli pochodzi z 'database_movies'.\n"
                
                "  * aktywnie poszukuj filmów, które spełniają kryterium o najwyższej wadze\n"
                "    ORAZ co najmniej jedno inne kryterium o wysokiej wadze.\n"
                
                "- Jeżeli taka kombinacja NIE istnieje,\n"
                "  DOPIERO WTEDY preferuj filmy spełniające wyłącznie\n"
                "  kryterium o najwyższej wadze.\n\n"


                "Ograniczenia twarde:\n"
                "- Film, który posiada tag o wadze -1, NIE MOŻE znaleźć się w wynikach.\n"
                "- Film, który NIE spełnia żadnego kryterium o najwyższej wadze, "
                "NIE MOŻE znaleźć się w TOP 10 rekomendacji.\n"
                "- Kryteria o niskiej wadze NIE MOGĄ generować rekomendacji samodzielnie.\n\n"

                "Przykład błędnej rekomendacji:\n"
                "- Film animowany bez elementów westernu (np. 'Madagascar') "
                "NIE POWINIEN zostać zarekomendowany, jeśli 'western' ma najwyższą wagę.\n"
                "- Film 'Die Hard' NIE POWINIEN zostać zarekomendowany, jeśli tag 'akcja' ma wagę -1.\n\n"

                "Jeśli musisz dodać filmy spoza database_movies, oznacz je jako synthesis=true "
                "i wyjaśnij powód w selection_reason.\n"
                "Dla synthesized=true:\n"
                "- selection_reason NIE może być ogólnym stwierdzeniem.\n"
                "- Musi odwoływać się do:\n"
                "  * kryterium o najwyższej wadze\n"
                "  * oraz (jeśli występuje) kryteriów bonusowych.\n"
                "- Przykład DOBREGO selection_reason:\n"
                "  'Added because the film strongly matches the primary western"
                " criterion (weight 7) through its setting and themes, and shows"
                " minor stylistic similarities to the animated preference (weight 2).'\n\n"


                "Zwróć odpowiedź WYŁĄCZNIE poprzez wywołanie funkcji "
                "'generate_recommendations'.\n\n"

                "WYMAGANA LICZBA WYNIKÓW:\n"
                "- ZAWSZE zwróć DOKŁADNIE 10 rekomendacji.\n"
                "- Jeżeli liczba filmów spełniających kryteria o najwyższej wadze "
                "jest mniejsza niż 10:\n"
                "* uzupełnij listę dodatkowymi filmami, "
                "które są NAJBLIŻSZE kryteriom o najwyższej wadze, "
                "nawet jeśli dopasowanie jest słabsze.\n"
                "* pamiętaj jednak o bezwzględnym ZAKAZIE z Etapu 0 (tag z wagą -1 wyklucza film zawsze).\n"
                "* takie filmy MUSZĄ mieć synthesis=true TYLKO JEŚLI filmu nie ma w 'database_movies'. "
                "oraz obniżone confidence ( < 0.3).\n"
                "- NIGDY nie skracaj listy rekomendacji."
            )
    }