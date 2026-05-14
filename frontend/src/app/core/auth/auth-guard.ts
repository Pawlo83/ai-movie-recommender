import { Injectable, inject } from '@angular/core';
import { CanActivate, Router } from '@angular/router';
import { AuthService } from './auth';
import { Observable, of } from 'rxjs';
import { map, catchError } from 'rxjs/operators';

// Serwis blokujący dostęp dla niezalogowanych użytkowników
@Injectable({
  providedIn: 'root'
})
export class AuthGuard implements CanActivate {
  private auth = inject(AuthService);
  private router = inject(Router);

  // Weryfikacja aktualnej sesji, przekierowanie do strony logowania przy niepowodzeniu
  canActivate(): Observable<boolean> {
    return this.auth.getCurrentUser().pipe(
      map(() => true),
      catchError(() => {
        this.router.navigate(['/admin/login']);
        return of(false);
      })
    );
  }
}