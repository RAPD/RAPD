import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { RunDialogComponent } from './run-dialog.component';

describe('RunDialogComponent', () => {
  let component: RunDialogComponent;
  let fixture: ComponentFixture<RunDialogComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ RunDialogComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(RunDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
