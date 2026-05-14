import { ComponentFixture, TestBed } from '@angular/core/testing';
import { SearchFormComponent } from './search-form.component';

describe('SearchFormComponent', () => {
  let component: SearchFormComponent;
  let fixture: ComponentFixture<SearchFormComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SearchFormComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(SearchFormComponent);
    component = fixture.componentInstance;
    component.availableTags = ['Action', 'Comedy', 'Drama', 'Horror'];
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should filter suggestions correctly', () => {
    component.tagRows[0].value = 'Act';
    const suggestions = component.getSuggestions(0);
    
    expect(suggestions).toContain('Action');
    expect(suggestions).not.toContain('Comedy');
  });

  it('should not allow submitting invalid form', () => {
    component.tagRows = [{ value: '', valid: true, rating: 4 }];
    component.description = '';
    
    expect(component.canSubmit()).toBeFalse();
  });

  it('should allow submitting valid form', () => {
    component.tagRows = [{ value: 'Action', valid: true, rating: 5 }];
    
    expect(component.canSubmit()).toBeTrue();
  });

  it('should detect duplicate tags', () => {
    component.tagRows = [
      { value: 'Action', valid: true, rating: 4 },
      { value: 'Action', valid: true, rating: 4 }
    ];

    component.checkValue();

    expect(component.tagRows[0].valid).toBeFalse();
    expect(component.tagRows[1].valid).toBeFalse();
  });
});