import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { SequenceDialogComponent } from './sequence-dialog.component';

describe('SequenceDialogComponent', () => {
  let component: SequenceDialogComponent;
  let fixture: ComponentFixture<SequenceDialogComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ SequenceDialogComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SequenceDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
