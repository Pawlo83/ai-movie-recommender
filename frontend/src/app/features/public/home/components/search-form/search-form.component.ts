import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

export interface TagRow {
  value: string;
  valid: boolean;
  rating: number;
  focused?: boolean;
}

export interface SearchPayload {
  criterions: { value: string; rating: number }[];
  description: string;
}

// Komponent formularza wyszukiwania filmów
@Component({
  selector: 'app-search-form',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './search-form.component.html',
  styleUrls: ['./search-form.component.css']
})
export class SearchFormComponent {
  @Input() availableTags: string[] = [];
  @Output() submitSearch = new EventEmitter<SearchPayload>();

  // Stan wierszy tagów
  tagRows: TagRow[] = [{ value: '', valid: true, rating: 4, focused: false }];
  
  // Indeksy podświetlonych sugestii w autouzupełnianiu
  highlightedIndex: number[] = [-1];
  
  description: string = '';
  
  // Ograniczenie liczby wyświetlanych podpowiedzi
  public maxVisibleLimit = 7;
  public visibleLimit = this.maxVisibleLimit;

  // Sprawdzenie czy wprowadzony tag nie jest duplikatem w innym wierszu
  checkValue(){
    this.tagRows.forEach(row => {
      const currentValLower = row.value.toLowerCase();
      const hasDuplicate = this.tagRows.some((r, i) => 
        r !== row && r.value.toLowerCase() === currentValLower && r.value!=''
      );
      row.valid = !hasDuplicate;
    });
  }

  // Aktualizacja limitu widocznych podpowiedzi (aby nie przekroczyć dostępnej liczby wyników)
  updateVisibleLimit(idx: number){
    const suggestions = this.getSuggestions(idx);
    if (!suggestions.length) return;
    this.visibleLimit = Math.min(suggestions.length, this.maxVisibleLimit);
  }

  // Obsługa wpisywania tekstu do pola tagu
  onValueChange(idx: number, newValue: string) {
    this.tagRows[idx].value = newValue;
    this.checkValue()
    
    // Automatyczne dodanie nowego pustego wiersza, jeśli edytujemy ostatni i jest poprawny
    if (this.tagRows[idx].valid && idx === this.tagRows.length - 1) {
      this.tagRows.push({ value: '', valid: true, rating: 4, focused: false });
      this.highlightedIndex.push(-1);
    }
    
    this.highlightedIndex[idx] = -1;
    this.updateVisibleLimit(idx)
  }

  // Ustawienie oceny dla danego kryterium
  setRating(idx: number, star: number) {
    this.tagRows[idx].rating = star;
  }

  // Przeniesienie kursora do następnego pola input
  focusNextInput(idx: number) {
    const inputEl = document.getElementById('input-' + (idx + 1));
    if (inputEl) {
      (inputEl as HTMLInputElement).focus();
    }
  }

  // Filtrowanie listy dostępnych tagów do sugestii
  getSuggestions(idx: number): string[] {
    const input = this.tagRows[idx].value.toLowerCase();
    return this.availableTags.filter(
      v =>
        v.toLowerCase().includes(input) &&
        !this.tagRows.some((row, i) => row.value === v && i !== idx)
    );
  }

  // Wybór tagu z listy podpowiedzi
  selectSuggestion(idx: number, tag: string) {
    this.onValueChange(idx, tag);
    setTimeout(() => {
      this.focusNextInput(idx);
    }, 0);
    this.highlightedIndex[idx] = -1;
  }

  // Obsługa nawigacji klawiaturą wewnątrz autouzupełnienia
  onKeyDown(idx: number, event: KeyboardEvent) {
    const suggestions = this.getSuggestions(idx);
    if (!suggestions.length) return;

    this.updateVisibleLimit(idx)

    if (event.key === 'ArrowDown') {
      event.preventDefault();
      if (this.highlightedIndex[idx] >= this.visibleLimit-1) {
        this.highlightedIndex[idx] = 0;
      } else {
        this.highlightedIndex[idx]++;
      }
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      if (this.highlightedIndex[idx] <= 0) {
          this.highlightedIndex[idx] = this.visibleLimit-1;
        } else {
          this.highlightedIndex[idx]--;
        }
    } else if (event.key === 'Enter') {
      event.preventDefault();
      this.visibleLimit = this.maxVisibleLimit;
      if (this.highlightedIndex[idx] >= 0) {
        this.selectSuggestion(idx, suggestions[this.highlightedIndex[idx]]);
      } else {
        this.focusNextInput(idx);
      }
    }
  }

  onFocus(idx: number) {
    this.tagRows[idx].focused = true;
    this.updateVisibleLimit(idx)  
  }

  // Usuwanie pustych wierszy po wyjściu z pola
  onBlur(idx: number) {
    this.tagRows[idx].focused = false;
    if (this.tagRows[idx].value.trim() === '' && idx < this.tagRows.length - 1) {
      this.removeRow(idx);
    }
  }

  removeRow(idx: number) {
    this.tagRows.splice(idx, 1);
    this.highlightedIndex.splice(idx, 1);
    this.checkValue()
  }

  // Walidacja globalna (wymagany przynajmniej jeden poprawny tag lub opis)
  canSubmit(): boolean {
    const hasTag = this.tagRows.some(row => row.valid && row.value.trim() !== '') && this.tagRows.every(row => row.valid);
    const hasDescription = Boolean(this.description) && (this.description.trim() !== '');
    return (hasTag || hasDescription);
  }

  // Zbudowanie payloadu i wysłanie zapytania
  onSubmit() {
    if (!this.canSubmit()) return;
    
    const payload: SearchPayload = {
      criterions: this.tagRows
        .filter(row => row.valid && row.value.trim() !== '')
        .map(row => ({ value: row.value.trim(), rating: row.rating })),
      description: this.description
    };
    
    this.submitSearch.emit(payload);

    // Automatyczne przewinięcie do sekcji wyników
    setTimeout(() => {
      const resultsElement = document.getElementById('app-results');
      
      if (resultsElement) {
        resultsElement.scrollIntoView({ 
          behavior: 'smooth',
          block: 'start'
        });
      }
    }, 100);
  }
}