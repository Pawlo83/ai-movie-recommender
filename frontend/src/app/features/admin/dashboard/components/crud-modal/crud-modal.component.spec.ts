import { ComponentFixture, TestBed } from '@angular/core/testing';
import { CrudModalComponent } from './crud-modal.component';

describe('CrudModalComponent', () => {
  let component: CrudModalComponent;
  let fixture: ComponentFixture<CrudModalComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CrudModalComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(CrudModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should emit correct payload for ADD', () => {
    spyOn(component.submitPayload, 'emit');
    
    component.mode = 'add';
    component.tableName = 'movies';
    component.currentRow = { name: 'New Movie', year: 2024, id: 999 };

    component.confirmTransaction();

    expect(component.submitPayload.emit).toHaveBeenCalledWith({
      table: 'movies',
      operation: 'add',
      values: { name: 'New Movie', year: 2024 }
    });
  });

    it('should emit only changed values for UPDATE', () => {
    spyOn(component.submitPayload, 'emit');

    component.mode = 'update';
    component.tableName = 'movies';
    component.columns = ['id', 'name', 'year'];
    
    component.inputRow = { id: 1, name: 'Old Name', year: 2000 };
    component.ngOnInit(); 
    component.currentRow.name = 'New Name'; 

    component.confirmTransaction();

    expect(component.submitPayload.emit).toHaveBeenCalledWith({
      table: 'movies',
      operation: 'update',
      id: 1,
      values: { name: 'New Name' }
    });
  });
});