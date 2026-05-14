import { Injectable, inject } from '@angular/core';
import {
  HttpEvent,
  HttpHandler,
  HttpInterceptor,
  HttpRequest,
  HttpErrorResponse
} from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, switchMap } from 'rxjs/operators';
import { AuthService } from './auth';
import { Router } from '@angular/router';
import { PublicService } from '../public/public';

// Interceptor automatycznie dołączający poświadczenia i obsługujący wygasłą sesję
@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  private auth = inject(AuthService);
  private router = inject(Router);
  private publicService = inject(PublicService);

  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    let headers = req.headers;
    const csrfToken = this.publicService.getToken();

    // Jeśli mamy token i metoda to nie GET -> dodaj nagłówek
    if (csrfToken && req.method !== 'GET' && req.method !== 'HEAD') {
      headers = headers.set('X-CSRFToken', csrfToken);
    }

    // Klonujemy z nowymi nagłówkami i credentials
    const authReq = req.clone({
      headers: headers,
      withCredentials: true
    });

    return next.handle(authReq).pipe(
      // Obsługa błędu 401: próba odświeżenia tokena i ponowienie żądania, wylogowanie w razie niepowodzenia
      catchError((error: HttpErrorResponse) => {
        if (error.status === 401 && !req.url.includes('/auth/token/refresh/')) {
          return this.auth.refreshToken().pipe(
            switchMap(() => {
              return next.handle(
                req.clone({ withCredentials: true })
              );
            }),
            catchError(() => {
              this.router.navigate(['/admin/login']);
              return throwError(() => error);
            })
          );
        }
        return throwError(() => error);
      })
    );
  }
}