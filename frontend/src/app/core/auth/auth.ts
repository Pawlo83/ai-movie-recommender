import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { Observable } from 'rxjs';

// Serwis obsługujący autentykację (logowanie, sesja, wylogowanie)
@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private http = inject(HttpClient);
  private apiUrl = environment.apiUrl;

  // Logowanie użytkownika i inicjalizacja sesji
  login(username: string, password: string): Observable<any> {
    return this.http.post(
      `${this.apiUrl}/auth/token/`,
      { username, password },
      { withCredentials: true }
    );
  }

  // Wylogowanie i usunięcie sesji po stronie serwera
  logout(): Observable<any> {
    return this.http.post(
      `${this.apiUrl}/auth/logout/`,
      {},
      { withCredentials: true }
    );
  }

  // Pobranie danych aktualnie zalogowanego użytkownika
  getCurrentUser(): Observable<any> {
    return this.http.get(
      `${this.apiUrl}/admin/me/`,
      { withCredentials: true }
    );
  }

  // Odświeżenie tokena autoryzacyjnego
  refreshToken(): Observable<any> {
    return this.http.post(
      `${this.apiUrl}/auth/token/refresh/`,
      {},
      { withCredentials: true }
    );
  }
}