import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ReintegrateDialogComponent } from './reintegrate-dialog.component';

describe('ReintegrateDialogComponent', () => {
  let component: ReintegrateDialogComponent;
  let fixture: ComponentFixture<ReintegrateDialogComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ReintegrateDialogComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ReintegrateDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
