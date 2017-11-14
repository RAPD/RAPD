import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ComponentsPanelComponent } from './components-panel.component';

describe('ComponentsPanelComponent', () => {
  let component: ComponentsPanelComponent;
  let fixture: ComponentFixture<ComponentsPanelComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ComponentsPanelComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ComponentsPanelComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
