import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { finalize } from 'rxjs/operators';

import { HeaderComponent } from './components/header/header.component';
import { SearchFormComponent, SearchPayload } from './components/search-form/search-form.component';
import { ResultsComponent } from './components/results/results.component';
import { WaitingScreenComponent } from './components/waiting-screen/waiting-screen.component';

import { PublicService } from '../../../core/public/public';

// Główny komponent strony głównej, integruje wyszukiwarkę, wyniki i ekrany ładowania
@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, HeaderComponent, SearchFormComponent, ResultsComponent, WaitingScreenComponent],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomeComponent implements OnInit {
  private publicService = inject(PublicService);

  // Dane aplikacji (tagi do autouzupełniania i lista filmów)
  possibleTags: string[] = [];
  recommendations: any[] = [];
  
  // Flagi stanu interfejsu
  isInitialLoading = false;
  isLoading = false;
  hasError = false;
  hasSearched = false;

  ngOnInit() {
    this.initPageData()
  }

  // Inicjalizacja danych dla strony
  initPageData() {
    this.isInitialLoading = true;

    // Sprawdzenie dostępności backendu
    this.publicService.getPing().subscribe({
      next: () => {
        // Sukces - pobieramy świeże dane (startowe rekomendacje i dostępne tagi)
        this.loadTags();
        this.loadDefaultRecs();
      },
      error: (err) => {
        // Porażka - pobranie lokalnych danych typu fallback
        console.error('API is offline, using fallbacks.', err);
        this.possibleTags = this.publicService.fallbackTags;
        this.recommendations = [];
        this.isInitialLoading = false;
      }
    });
  }

  // Pobranie listy tagów z backendu
  loadTags() {
    this.publicService.getInitialTags().subscribe({
      next: (tags) => this.possibleTags = tags,
      error: (err) => {
        console.error('Failed to init tags', err)
        this.possibleTags = this.publicService.fallbackTags;
      }
    });
  }

  // Pobranie startowych rekomendacji
  loadDefaultRecs() {
    this.publicService.getDefaultRecommendations().subscribe({
      next: (recs) => {
        this.recommendations = recs;
        this.isInitialLoading = false;
      },
      error: (err) => {
        console.error('Failed to init recs', err)
        this.recommendations = [];
        this.isInitialLoading = false;
      }
    });
  }

  // Obsługa zdarzenia wyszukiwania (zapytanie do backendu i aktualizacja wyników)
  handleSearch(payload: SearchPayload) {
    this.isLoading = true;
    this.hasError = false;
    this.hasSearched = false;
    this.recommendations = [];

    this.publicService.getRecommendations(payload)
      .pipe(
        finalize(() => this.isLoading = false)
      )
      .subscribe({
        next: (recs) => {
          this.recommendations = recs;
          this.hasSearched = true;
        },
        error: (err) => {
          console.error('Recs failed', err);
          this.hasError = true;
          this.hasSearched = true;
        }
      });
  }
}