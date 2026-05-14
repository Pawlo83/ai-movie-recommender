import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

// Komponent wyświetlający ekran oczekiwania
@Component({
  selector: 'app-waiting-screen',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './waiting-screen.component.html',
  styleUrls: ['./waiting-screen.component.css']
})
export class WaitingScreenComponent {
  // Flaga rozróżniająca wstępne ładowanie aplikacji od oczekiwania na wyniki wyszukiwania
  @Input() isInitialLoading = false;
}