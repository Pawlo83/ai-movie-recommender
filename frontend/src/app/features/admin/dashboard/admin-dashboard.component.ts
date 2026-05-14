import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { interval, Subscription } from 'rxjs';
import { switchMap } from 'rxjs/operators';
import { AuthService } from '../../../core/auth/auth';
import { AdminService } from '../../../core/admin/admin';

// Sub-komponenty
import { HeaderComponent } from './components/header/header.component';
import { DataTableComponent } from './components/data-table/data-table.component';
import { CrudModalComponent } from './components/crud-modal/crud-modal.component';
import { TagsModalComponent } from './components/tags-modal/tags-modal.component';

// Główny komponent panelu administratora, integruje tabele danych, modale CRUD i zarządzanie sesją
@Component({
  selector: 'app-admin-dashboard',
  standalone: true,
  imports: [CommonModule, HeaderComponent, DataTableComponent, CrudModalComponent, TagsModalComponent],
  templateUrl: './admin-dashboard.component.html',
  styleUrls: ['./admin-dashboard.component.css']
})
export class AdminDashboardComponent implements OnInit, OnDestroy {
  private authService = inject(AuthService);
  private adminService = inject(AdminService);
  private router = inject(Router);

  // Stan danych tabeli
  availableTables: string[] = [];
  selectedTableName: string | null = null;
  tableData: any[] = [];
  tableColumns: string[] = [];
  
  // Stan interfejsu
  isLoading = false;
  isLoadingTags = false;
  errorMessage = '';
  
  // Konfiguracja modala CRUD
  modalMode: 'add' | 'update' | 'delete' | null = null;
  selectedRow: any = {}; 
  
  // Konfiguracja modala tagów
  showTagsModal = false;
  filmTags: string[] = [];
  currentFilmId: string | null = null;
  currentFilmTitle: string | null = null;

  private heartbeatSub: Subscription | null = null;

  ngOnInit() {
    this.loadTableList();
    this.startHeartbeat();
  }

  ngOnDestroy() {
    if (this.heartbeatSub) this.heartbeatSub.unsubscribe();
  }

  // Cykliczne sprawdzanie sesji co 30 sekund
  startHeartbeat() {
    this.heartbeatSub = interval(30000)
    .pipe(
      switchMap(() => this.authService.getCurrentUser())
    )
    .subscribe({
      next: (data) => { },
      error: (err) => {
        if (err.status === 401 || err.status === 403) {
          alert('Session expired. Logging out...');
          this.forceLogout();
        }
      }
    });
  }

  // Wymuszenie wylogowania po wygaśnięciu sesji
  forceLogout() {
    if (this.heartbeatSub) {
      this.heartbeatSub.unsubscribe();
    }
    this.logout();
  }

  // Procedura wylogowania
  logout() {
    this.authService.logout().subscribe({
      next: () => this.router.navigate(['/admin/login']),
      error: () => this.router.navigate(['/admin/login'])
    });
  }

  // Pobranie listy dostępnych tabel z bazy danych
  loadTableList() {
    this.isLoading = true;
    this.adminService.getAllTables().subscribe({
      next: (data) => {
        console.log('Received table list:', data);
        this.availableTables = data.tables.map((t: { name: string; }) => t.name);
        this.isLoading = false;
        console.log(this.availableTables)
      },
      error: (err) => {
        console.error('Error fetching tables:', err);
        this.errorMessage = 'Could not load database tables.';
        this.isLoading = false;
      }
    });
  }

  // Wybór tabeli i załadowanie jej zawartości
  selectTable(name: string) {
    this.selectedTableName = name;
    this.refreshTable();
  }

  // Odświeżenie danych dla aktualnie wybranej tabeli
  refreshTable() {
    if (!this.selectedTableName) return;
    this.isLoading = true;
    this.errorMessage = '';
    
    this.adminService.getTableData(this.selectedTableName).subscribe({
      next: (data) => {
        const rows = data.data || data;
        this.tableData = rows;
        this.tableColumns = rows.length > 0 ? Object.keys(rows[0]) : [];
        this.isLoading = false;
      },
      error: () => {
        this.errorMessage = `Could not load data for ${this.selectedTableName}.`;
        this.isLoading = false;
      }
    });
  }

  // Otwieranie modali w odpowiednich trybach
  openAdd() {
    this.modalMode = 'add';
    this.selectedRow = {};
  }
  
  openEdit(row: any) {
    this.modalMode = 'update';
    this.selectedRow = row;
  }
  
  openDelete(row: any) {
    this.modalMode = 'delete';
    this.selectedRow = row;
  }
  
  closeModals() {
    this.modalMode = null;
    this.showTagsModal = false;
    this.selectedRow = {};
  }

  // Wykonanie operacji CRUD
  handleCrudAction(payload: any) {
    this.adminService.modifyData(payload).subscribe({
      next: (response) => {
        if (response.success === true) {
          this.closeModals();
          this.refreshTable();
        } else {
          alert('Operation failed: ' + response.message);
        }
      },
      error: (err) => {
        console.error('Transaction failed:', err);
        alert('Operation failed.');
      }
    });
  }

  // Otwieranie modalu tagów dla wybranego filmu
  openTags(row: any) {
    this.currentFilmId = row.id;
    this.currentFilmTitle = row.name;
    this.fetchTags();
  }

  // Pobranie aktualnych tagów dla filmu
  fetchTags() {
    if (!this.currentFilmId) return;
    this.isLoadingTags = true;
    this.adminService.manageFilmTags({ action: 'get', film_id: this.currentFilmId }).subscribe({
      next: (data: any) => {
        this.filmTags = data || [];
        this.showTagsModal = true;
        this.isLoadingTags = false;
      },
      error: (err) => {
        console.error('Error fetching tags:', err);
        this.errorMessage = `Failed to load tags for <i>${this.currentFilmTitle}</i>.`;
        this.isLoadingTags = false;
      }
    });
  }

  // Zapisanie zmian w tagach
  handleTagAction(payload: any) {
    this.isLoadingTags = true;
    this.adminService.manageFilmTags(payload).subscribe({
      next: () => {
        this.fetchTags();
        this.isLoadingTags = false;
      },
      error: (err) => {
        this.isLoadingTags = false;
        alert('Tag operation failed');
        console.error(err);
      }
    });
  }
}