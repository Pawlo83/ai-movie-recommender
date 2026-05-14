import { Injectable, signal, effect, inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';

// Serwis zarządzający motywem aplikacji
@Injectable({
  providedIn: 'root',
})
export class Theme {
  private platformId = inject(PLATFORM_ID);
  
  // Sygnał przechowujący aktualny stan motywu
  darkModeSignal = signal<'light' | 'dark'>('light');

  constructor() {
    // Sprawdzenie czy kod działa w przeglądarce
    if (isPlatformBrowser(this.platformId)) {
      const storedTheme = localStorage.getItem('theme') as 'light' | 'dark';
      
      // Ustawienie motywu na podstawie zapisanych ustawień lub preferencji systemowych
      if (storedTheme) {
        this.darkModeSignal.set(storedTheme);
      } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
        this.darkModeSignal.set('dark');
      }

      // Aktualizacja klasy CSS i zapis do localStorage
      effect(() => {
        const theme = this.darkModeSignal();
        
        if (theme === 'dark') {
          document.body.classList.add('dark-mode');
        } else {
          document.body.classList.remove('dark-mode');
        }

        localStorage.setItem('theme', theme);
      });
    }
  }

  // Przełączenie motywu na przeciwny
  toggleTheme() {
    this.darkModeSignal.update(current => (current === 'light' ? 'dark' : 'light'));
  }
}