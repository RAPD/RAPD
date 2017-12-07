import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { DialogNewProjectComponent } from './dialog-new-project.component';

describe('DialogNewProjectComponent', () => {
  let component: DialogNewProjectComponent;
  let fixture: ComponentFixture<DialogNewProjectComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ DialogNewProjectComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DialogNewProjectComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
