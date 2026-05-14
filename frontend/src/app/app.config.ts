import { ApplicationConfig, provideBrowserGlobalErrorListeners, provideZoneChangeDetection } from '@angular/core';
import { provideRouter } from '@angular/router';
import { HTTP_INTERCEPTORS, provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { DATE_PIPE_DEFAULT_OPTIONS } from '@angular/common';

import { routes } from './app.routes';
import { AuthInterceptor } from './core/auth/auth-interceptor';

// Główna konfiguracja aplikacji
export const appConfig: ApplicationConfig = {
  providers: [
    // Obsługa globalnych błędów przeglądarki
    provideBrowserGlobalErrorListeners(),

    // Optymalizacja detekcji zmian
    provideZoneChangeDetection({ eventCoalescing: true }),

    // Konfiguracja routingu
    provideRouter(routes),

    // Klient HTTP z włączoną obsługą klasycznych interceptorów
    provideHttpClient(withInterceptorsFromDi()),
    {
      provide: HTTP_INTERCEPTORS,
      useClass: AuthInterceptor,
      multi: true
    },

    // Ustawienie domyślnego formatu daty dla całej aplikacji
    {
      provide: DATE_PIPE_DEFAULT_OPTIONS,
      useValue: { dateFormat: 'dd.MM.yyyy' }
    }
  ]
};