import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';

// Komponent nagłówka panelu administratora
@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.css']
})
export class HeaderComponent {
  // Lista dostępnych tabel przekazana z komponentu nadrzędnego
  @Input() tables: string[] = [];
  
  // Nazwa aktualnie wybranej tabeli
  @Input() selectedTableName: string | null = null;
  
  // Emisja zdarzenia po naciśnięciu w nazwę tabeli
  @Output() tableSelect = new EventEmitter<string>();
  
  // Sygnał żądania wylogowania
  @Output() logout = new EventEmitter<void>();
}