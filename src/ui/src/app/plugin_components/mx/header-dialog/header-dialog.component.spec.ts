import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { HeaderDialogComponent } from './header-dialog.component';

describe('HeaderDialogComponent', () => {
  let component: HeaderDialogComponent;
  let fixture: ComponentFixture<HeaderDialogComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ HeaderDialogComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(HeaderDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should be created', () => {
    expect(component).toBeTruthy();
  });
});
