import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Theme } from '../../../../../core/theme/theme';

// Komponent nagłówka strony głównej
@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.css']
})
export class HeaderComponent {
  // Wstrzyknięcie serwisu do obsługi motywu
  themeService = inject(Theme);
}