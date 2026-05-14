import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { finalize } from 'rxjs/operators';
import { Router } from '@angular/router';
import { AuthService } from '../../../core/auth/auth';
import { PublicService } from '../../../core/public/public';

// Komponent obsługujący formularz logowania do panelu administatora
@Component({
  selector: 'app-admin-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './admin-login.html',
  styleUrls: ['./admin-login.css']
})
export class AdminLoginComponent implements OnInit{
  // Stan formularza i interfejsu
  username = '';
  password = '';
  error = '';
  isLoading = false;
  isServerReady = false;
  isServerOffline = false;

  private publicService = inject(PublicService);
  private auth = inject(AuthService);
  private router = inject(Router);

  ngOnInit() {
    // Sprawdzenie dostępności backendu
    this.publicService.getPing().subscribe({
      next: () => { 
        this.isServerReady = true;
      },
      error: (err) => {
        console.error('API is offline.', err);
        this.isServerReady = false;
        this.isServerOffline = true;
      }
    });
  }

  // Obsługa logowania, autentykacja i przekierowanie do dashboardu lub wyświetlenie błędu
  onSubmit(): void {
    if (this.isLoading) return;

    this.error = '';
    this.isLoading = true;

    this.auth.login(this.username, this.password).pipe(
      finalize(() => this.isLoading = false)
    ).subscribe({
      next: () => {
        this.router.navigate(['/admin']);
      },
      error: () => {
        this.error = 'Invalid credentials';
      }
    });
  }
}