import { ComponentFixture, TestBed } from '@angular/core/testing';
import { DataTableComponent } from './data-table.component';

describe('DataTableComponent', () => {
  let component: DataTableComponent;
  let fixture: ComponentFixture<DataTableComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DataTableComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(DataTableComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should sort data alphabetically ascending', () => {
    component.data = [{ name: 'B' }, { name: 'A' }, { name: 'C' }];
    component.sortColumn = 'name';
    component.sortDirection = 'asc';

    component.sortData();

    expect(component.data[0].name).toBe('A');
    expect(component.data[2].name).toBe('C');
  });

  it('should sort data numerically descending', () => {
    component.data = [{ id: 10 }, { id: 50 }, { id: 5 }];
    component.sortColumn = 'id';
    component.sortDirection = 'desc';

    component.sortData();

    expect(component.data[0].id).toBe(50);
    expect(component.data[2].id).toBe(5);
  });
});