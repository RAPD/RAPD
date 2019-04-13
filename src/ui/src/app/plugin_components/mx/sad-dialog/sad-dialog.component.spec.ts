import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { SadDialogComponent } from './sad-dialog.component';

describe('SadDialogComponent', () => {
  let component: SadDialogComponent;
  let fixture: ComponentFixture<SadDialogComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ SadDialogComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SadDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
