import { Component, Input, OnDestroy, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PublicService } from '../../../../../core/public/public';

type AnimationState = 'enter' | 'exit' | 'hidden';

// Komponent wyświetlający wyniki wyszukiwania oraz ekran ładowania z ciekawostkami
@Component({
  selector: 'app-results',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './results.component.html',
  styleUrls: ['./results.component.css']
})
export class ResultsComponent implements OnDestroy {
  private publicService = inject(PublicService);

  @Input() recommendations: any[] = [];
  @Input() hasError = false;
  @Input() hasSearched = false;

  // Stan widoku (Siatka vs Lista)
  isGridView: boolean = true;

  // Indeksy paginacji dla listy dostawców filmu
  providerIndices: { [key: number]: number } = {};

  private _isLoading = false;
  
  // Sterowanie logiką ładowania
  @Input()
  set isLoading(value: boolean) {
    this._isLoading = value;
    if (value) { this.resetAndStartLoop(); } 
    else { this.stopLoop(); }
  }
  get isLoading(): boolean {
    return this._isLoading;
  }

  // Zmienne obsługujące animację ciekawostek
  private loopTimeoutId: any;
  currentFactIndex: number = 0;
  animationState = signal<AnimationState>('hidden');
  funFacts = this.publicService.funFacts;

  ngOnDestroy() {
    this.stopLoop();
  }

  // Przełączanie widoku i resetowanie stanu paginacji dostawców
  toggleView(isGrid: boolean) {
    this.isGridView = isGrid;
    this.providerIndices = {};
  }

  // Zmiana ilości wyświetlanych dostawców zależny od widoku 
  get providerPageSize(): number {
    return this.isGridView ? 5 : 12;
  }

  getProviderStart(index: number): number {
    return this.providerIndices[index] || 0;
  }

  // Przewijanie listy dostawców
  nextProviders(index: number, total: number) {
    const current = this.getProviderStart(index);
    if (current + this.providerPageSize < total) {
      this.providerIndices[index] = current + this.providerPageSize;
    }
  }
  prevProviders(index: number, total: number) {
    const current = this.getProviderStart(index);
    if (current - this.providerPageSize < total) {
      this.providerIndices[index] = current - this.providerPageSize;
    }
  }

  // Źródło obrazów dla filmów w ui
  tmdbBaseUrl: string = this.publicService.tmdbBaseUrl;

  // Ukrywanie obrazu w przypadku błędu ładowania
  handleMissingImage(event: Event) {
    const imgElement = event.target as HTMLImageElement;
    imgElement.style.display = 'none';
  }

  // Losowanie kolejności ciekawostek
  private shuffleFacts() {
    for (let i = this.funFacts.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [this.funFacts[i], this.funFacts[j]] = [this.funFacts[j], this.funFacts[i]];
    }
  }

  // Stopowanie animacji ciekawostek
  private stopLoop() {
    if (this.loopTimeoutId) {
      clearTimeout(this.loopTimeoutId);
      this.loopTimeoutId = null;
    }
  }

  // Resetowanie animacji ciekawostek
  private resetAndStartLoop() {
    this.stopLoop();
    this.shuffleFacts();
    this.currentFactIndex = 0;
    this.runAnimationLoop();
  }

  // Rekurencyjna pętla sterująca stanami animacji (enter -> exit -> hidden -> next)
  runAnimationLoop() {
    this.animationState.set('enter');
    // Czas wyświetlania tekstu (10.5s)
    this.loopTimeoutId = setTimeout(() => {
      this.animationState.set('exit')
      // Czas na animację wyjścia (0.5s)
      this.loopTimeoutId = setTimeout(() => {
        this.animationState.set('hidden');
        this.currentFactIndex = (this.currentFactIndex + 1) % this.funFacts.length;
        // Pauza przed kolejnym wejściem (0.5s)
        this.loopTimeoutId = setTimeout(() => {
          this.runAnimationLoop();
        }, 500);
      }, 500);
    }, 10500);
  }
}