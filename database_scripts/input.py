import re

# Skrypt pozwalający na sprawne przekształcenie inputu z rankingu filmów w format dzięki któremu znajdziemy dany film w TMDB API (Title|Year).

raw_data = """1	Avatar	$2,923,710,708	2009
2	Avengers: Endgame	$2,799,439,100	2019
3	Avatar: The Way of Water	$2,343,477,301	2022
4	Titanic	$2,264,812,968	1997
5	Ne Zha 2	$2,150,000,000	2025
6	Star Wars: Episode VII - The Force Awakens	$2,071,310,218	2015
7	Avengers: Infinity War	$2,052,415,039	2018
8	Spider-Man: No Way Home	$1,921,426,073	2021
9	Inside Out 2	$1,698,863,816	2024
10	Jurassic World	$1,671,537,444	2015"""

movie_entries = []

for line in raw_data.split('\n'):
    if line:
        # Regex wyjaśnienie:
        # ^\d+\s+       -> Numer rankingu na początku i odstęp
        # (.*?)         -> GRUPA 1: Tytuł (bierze wszystko aż do...)
        # \s+\$[\d,]+   -> ...odstępu, znaku $ i ciągu cyfr z przecinkami (kwota)
        # \s+           -> odstęp
        # (\d{4})       -> GRUPA 2: Rok (dokładnie 4 cyfry)
        match = re.search(r'^\d+\s+(.*?)\s+\$[\d,]+\s+(\d{4})', line)
        
        if match:
            title = match.group(1).strip()
            year = match.group(2)
            # Tworzymy format: Tytul|Rok
            movie_entries.append(f"{title}|{year}")

# Wynik łączymy średnikami, ale wewnątrz mamy 'Title|Year'
print(f'python script.py --movies "{";".join(movie_entries)}"')