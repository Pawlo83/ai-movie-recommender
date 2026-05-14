import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { Observable } from 'rxjs';
import { map, tap } from 'rxjs/operators';


export interface SearchPayload {
  criterions: any[];
  description: string;
}

export interface TagResponse {
  tags: { tag_name: string }[];
}

export interface RecommendationResponse {
  recommendations: any[];
}

interface PingResponse {
  status: string;
  csrf_token: string; 
}

// Serwis części publicznej dostarczający dane dla strony głównej
@Injectable({
  providedIn: 'root'
})
export class PublicService {
  private http = inject(HttpClient);
  private apiUrl = environment.apiUrl;
  private csrfToken: string | null = null;

  tmdbBaseUrl: string = "https://image.tmdb.org/t/p/w500";

  // Statyczna lista tagów używana jako fallback w przypadku błędu API
  fallbackTags: string[] = [
    "friendship", "adventure", "adaptation", "self-discovery", "duringcreditsstinger",
    "sequel", "comedy", "action", "survival", "aftercreditsstinger",
    "coming of age", "hero's journey", "redemption", "villain", "family",
    "superhero", "based on comic", "betrayal", "teamwork", "fantasy",
    "family dynamics", "humor", "mystery", "action-packed", "revenge",
    "new york city", "family-friendly", "california", "amused", "team dynamics",
    "animation", "identity crisis", "sacrifice", "moral dilemmas", "romantic comedy",
    "personal growth", "moral ambiguity", "spy", "exploration", "thriller",
    "intense", "psychological thriller", "whimsical", "magic", "nostalgia",
    "heroic journey", "musical", "suspenseful", "courage", "social commentary"
  ];

  // Ciekawostki filmowe wyświetlane na ekranie ładowania
  funFacts: string[] = [
    "The 24 fps standard exists largely because it was the slowest frame rate that still allowed synchronized sound without audible distortion, saving film stock in the 1920s.",
    "The Wilhelm scream is an iconic stock sound effect that has been used in many films, television programs and other media. It was originated from a 1951 Warner Bros. sound library and was named decades later by sound designer Ben Burtt.",
    "Motion blur in movies isn't “realistic” — It's an artifact resulting from a 180-degree shutter angle, inherited from mechanical film cameras.",
    "Movie “night scenes” are often filmed during the day using day-for-night techniques with underexposure and blue tinting.",
    "Actors often deliver emotional performances to tennis balls or taped X's, which are later replaced with CGI characters.",
    "In The Dark Knight, Heath Ledger actually improvised the slow clap in the jail cell scene—Nolan kept rolling.",
    "In Blade Runner 2049, Ryan Gosling barely blinks in many scenes to create an unnerving, inhuman calm.",
    "In Se7en, Brad Pitt's confusion during the final scene was heightened because he didn't know what was in the box until the day of shooting.",
    "Leonardo DiCaprio cut his hand for real in Django Unchained and stayed in character while bleeding.",
    "True IMAX film uses 70mm horizontal film with 15 perforations per frame, making each frame about 10x larger than 35mm.",
    "Some IMAX cameras are so rare that fewer than 10 units exist worldwide at any given time.",
    "Popcorn became the iconic movie snack mostly by accident—through economics, timing, and a bit of cultural luck."
  ];

  // Prosty ping sprawdzający dostępność backendu
  getPing(): Observable<any> {
    return this.http.get<PingResponse>(`${this.apiUrl}/meta/ping/`, {
      withCredentials: true
    }).pipe(
      tap(response => {
        if (response.csrf_token) {
          this.csrfToken = response.csrf_token;
        }
      })
    );
  }

  // Metoda dla Interceptora
  getToken(): string | null {
    return this.csrfToken;
  }

  // Pobranie dostępnych tagów z backendu i spłaszczenie struktury do tablicy stringów
  getInitialTags(): Observable<string[]> {
    return this.http.get<TagResponse>(`${this.apiUrl}/meta/tags/`, {}).pipe(
      map(response => response.tags.map(t => t.tag_name))
    );
  }

  // Pobranie startowych rekomendacji
  getDefaultRecommendations(): Observable<any[]> {
    return this.http.get<RecommendationResponse>(`${this.apiUrl}/recommendations/default`, {}).pipe(
      map(response => response.recommendations)
    );
  }

  // Wyszukiwanie rekomendacji na podstawie kryteriów i opisu
  getRecommendations(payload: SearchPayload): Observable<any[]> {
    const req = {
       criterions: payload.criterions,
       description: payload.description
    };
    
    return this.http.post<RecommendationResponse>(`${this.apiUrl}/recommendations/`, { req }).pipe(
      map(response => response.recommendations)
    );
  }
}