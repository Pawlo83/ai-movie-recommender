import { Component, EventEmitter, Input, Output, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';

// Komponent wyświetlający dane w tabeli z obsługą sortowania i akcji CRUD
@Component({
  selector: 'app-data-table',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './data-table.component.html',
  styleUrls: ['./data-table.component.css']
})
export class DataTableComponent implements OnChanges {
  // Dane wejściowe i stan interfejsu
  @Input() tableName: string | null = null;
  @Input() data: any[] = [];
  @Input() columns: string[] = [];
  @Input() isLoading = false;
  @Input() errorMessage = '';

  // Zdarzenia emitowane do komponentu nadrzędnego
  @Output() refresh = new EventEmitter<void>();
  @Output() openAdd = new EventEmitter<void>();
  @Output() openEdit = new EventEmitter<any>();
  @Output() openDelete = new EventEmitter<any>();
  @Output() openTags = new EventEmitter<any>();

  // Lokalny stan sortowania
  sortColumn: string = '';
  sortDirection: 'asc' | 'desc' = 'asc';

  // Reakcja na zmiany wybranej tabeli, sortowania oraz danych
  ngOnChanges(changes: SimpleChanges) {
    if (changes['tableName'] && !changes['tableName'].firstChange) {
      this.sortColumn = '';
      this.sortDirection = 'asc';
    }
    
    if (changes['data'] && this.sortColumn) {
      this.sortData();
    }
  }

  // Ustawienie kolumny sortowania lub odwrócenie kierunku
  onSort(column: string) {
    if (this.sortColumn === column) {
      this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      this.sortColumn = column;
      this.sortDirection = 'asc';
    }
    this.sortData();
  }

  // Sortowanie po stronie klienta
  sortData() {
    if (!this.sortColumn || !this.data) return;

    this.data.sort((a, b) => {
      const valA = a[this.sortColumn];
      const valB = b[this.sortColumn];

      if (valA === null || valA === undefined) return 1;
      if (valB === null || valB === undefined) return -1;

      const strA = String(valA).toLowerCase();
      const strB = String(valB).toLowerCase();

      // Sortowanie alfanumeryczne
      const comparison = strA.localeCompare(strB, undefined, { numeric: true, sensitivity: 'base' });

      return this.sortDirection === 'asc' ? comparison : -comparison;
    });
  }

  // Helper sprawdzający czy wartość jest obiektem (dla poprawnego wyświetlania w HTML)
  isObject(val: any): boolean {
    return typeof val === 'object' && val !== null;
  }
}