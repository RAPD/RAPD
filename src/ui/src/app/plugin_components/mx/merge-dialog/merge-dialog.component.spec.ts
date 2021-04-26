import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MergeDialogComponent } from './merge-dialog.component';

describe('MergeDialogComponent', () => {
  let component: MergeDialogComponent;
  let fixture: ComponentFixture<MergeDialogComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ MergeDialogComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(MergeDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
