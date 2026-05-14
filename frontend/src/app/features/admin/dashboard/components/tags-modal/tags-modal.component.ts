import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

// Komponent formularza zarządzającego tagami dla konkretnego filmu
@Component({
  selector: 'app-tags-modal',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './tags-modal.component.html',
  styleUrls: ['./tags-modal.component.css']
})
export class TagsModalComponent {
  // Dane filmu i lista aktualnych tagów
  @Input() tags: string[] = [];
  @Input() filmTitle: string | null = '';
  @Input() filmId: string | null = null;
  @Input() isLoading = false;
  
  // Sygnały zamknięcia modala i wykonania akcji na tagach
  @Output() close = new EventEmitter<void>();
  @Output() tagAction = new EventEmitter<any>();

  newTagName = '';

  // Walidacja i wysłanie żądania dodania nowego tagu
  prepareAddTag() {
    if (!this.newTagName.trim()) return;
    
    const payload = {
      action: 'add',
      film_id: this.filmId,
      tag_name: this.newTagName.trim()
    };
    
    this.tagAction.emit(payload);
    this.newTagName = '';
  }

  // Wysłanie żądania usunięcia istniejącego tagu
  prepareRemoveTag(tagName: string) {
    const payload = {
      action: 'remove',
      film_id: this.filmId,
      tag_name: tagName
    };
    this.tagAction.emit(payload);
  }
}