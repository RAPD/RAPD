import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { MrDialogComponent } from './mr-dialog.component';

describe('MrDialogComponent', () => {
  let component: MrDialogComponent;
  let fixture: ComponentFixture<MrDialogComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ MrDialogComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MrDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
