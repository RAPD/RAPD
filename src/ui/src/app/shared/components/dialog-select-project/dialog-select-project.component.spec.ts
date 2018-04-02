import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { DialogSelectProjectComponent } from './dialog-select-project.component';

describe('DialogSelectProjectComponent', () => {
  let component: DialogSelectProjectComponent;
  let fixture: ComponentFixture<DialogSelectProjectComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ DialogSelectProjectComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DialogSelectProjectComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
