import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { DialogUglymolComponent } from './dialog-uglymol.component';

describe('DialogUglymolComponent', () => {
  let component: DialogUglymolComponent;
  let fixture: ComponentFixture<DialogUglymolComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ DialogUglymolComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DialogUglymolComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
