import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { HttpParams } from '@angular/common/http';

// Serwis obsługujący operacje administra, odpowiada za pobieranie struktur tabel, danych oraz ich modyfikację w bazie
@Injectable({
  providedIn: 'root'
})
export class AdminService {
  private http = inject(HttpClient);
  private apiUrl = environment.apiUrl;

  // Pobranie listy wszystkich dostępnych tabel w systemie
  getAllTables(): Observable<any> {
    return this.http.get(`${this.apiUrl}/admin/tables/`);
  }

  getTableData(tableName: string): Observable<any> {
    const params = new HttpParams().set('table_name', tableName + '_view');
    return this.http.get(`${this.apiUrl}/admin/tables/data/`, { params: params });
  }

  // Wysyłanie modyfikacji danych (CRUD) w odpowiednim formacie
  modifyData(payload: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/admin/tables/modify/`, payload);
  }

  // Obsługa pobierania, dodawania i usuwania tagów dla filmów
  manageFilmTags(payload: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/admin/film-tags/`, payload);
  }
}