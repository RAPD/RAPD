import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { OverwatchesPanelComponent } from './overwatches-panel.component';

describe('OverwatchesPanelComponent', () => {
  let component: OverwatchesPanelComponent;
  let fixture: ComponentFixture<OverwatchesPanelComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ OverwatchesPanelComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(OverwatchesPanelComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
