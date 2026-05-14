import { Component, EventEmitter, Input, Output, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

// Komponent formularza obsługującego operacje CRUD
@Component({
  selector: 'app-crud-modal',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './crud-modal.component.html',
  styleUrls: ['./crud-modal.component.css']
})
export class CrudModalComponent implements OnInit {
  // Konfiguracja trybu pracy i dane wejściowe
  @Input() mode: 'add' | 'update' | 'delete' | null = null;
  @Input() columns: string[] = [];
  @Input() inputRow: any = {};
  @Input() tableName: string | null = null;
  
  // Zdarzenia sterujące
  @Output() close = new EventEmitter<void>();
  @Output() submitPayload = new EventEmitter<any>();

  // Lokalne kopie edytowanych danych
  currentRow: any = {};
  originalRow: any = {};

  // Klonowanie danych wejściowych, by nie modyfikować bezpośrednio widoku tabeli przed zatwierdzeniem zmian
  ngOnInit() {
    this.currentRow = { ...this.inputRow };
    this.originalRow = { ...this.inputRow };
  }

  // Przygotowanie payloadu transakcji w zależności od trybu
  confirmTransaction() {
    let operation = this.mode;
    
    // Automatyczne wykrycie klucza głównego (ID/UUID) lub pobranie pierwszej kolumny jako fallback
    let idKey = this.columns.find(col => col.toLowerCase() === 'id' || col.toLowerCase() === 'uuid');
    if (!idKey && this.columns.length > 0) idKey = this.columns[0];
    const recordId = idKey ? this.currentRow[idKey] : null;

    let payload: any = {
      table: this.tableName,
      operation: operation
    };

    // Pola ignorowane przy tworzeniu nowych rekordów
    const ignoredFields = ['id', 'uuid', 'created_at', 'modified_at', 'updated_at'];

    if (operation === 'delete') {
      payload.id = recordId;
    }
    else if (operation === 'update') {
      payload.id = recordId;
      const changedValues: any = {};
      
      // Wykrywanie różnic (wysyłamy tylko pola, które uległy zmianie)
      Object.keys(this.currentRow).forEach(key => {
        if (this.currentRow[key] !== this.originalRow[key]) {
          changedValues[key] = this.currentRow[key];
        }
      });
      
      if (Object.keys(changedValues).length === 0) {
        alert('No changes detected.');
        return;
      }
      payload.values = changedValues;
    }
    else if (operation === 'add') {
      const valuesToSend = { ...this.currentRow };
      
      // Usunięcie zbędnych pól przed wysłaniem
      Object.keys(valuesToSend).forEach(key => {
        if (ignoredFields.includes(key.toLowerCase())) delete valuesToSend[key];
      });
      payload.values = valuesToSend;
    }

    this.submitPayload.emit(payload);
  }
}