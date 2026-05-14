import { Routes } from '@angular/router';
import { HomeComponent } from './features/public/home/home.component';
import { AdminLoginComponent } from './features/admin/login/admin-login';
import { AdminDashboardComponent } from './features/admin/dashboard/admin-dashboard.component';
import { AuthGuard } from './core/auth/auth-guard';

// Główna konfiguracja nawigacji aplikacji
export const routes: Routes = [
  // Strona główna
  {
    path: '',
    component: HomeComponent,
    title: 'MovieTell'
  },
  // Strona logowania do panelu administratora
  {
    path: 'admin/login',
    component: AdminLoginComponent,
    title: 'Admin Panel - Login'
  },
  // Panel administratora
  {
    path: 'admin',
    component: AdminDashboardComponent,
    canActivate: [AuthGuard],
    title: 'Admin Panel'
  },
  // Przekierowanie wszystkich nieznanych adresów na stronę główną
  {
    path: '**',
    redirectTo: ''
  }
];