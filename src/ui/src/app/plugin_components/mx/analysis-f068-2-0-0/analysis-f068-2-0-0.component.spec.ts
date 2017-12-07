import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { AnalysisF068200Component } from './analysis-f068-2-0-0.component';

describe('AnalysisF068200Component', () => {
  let component: AnalysisF068200Component;
  let fixture: ComponentFixture<AnalysisF068200Component>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ AnalysisF068200Component ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AnalysisF068200Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should be created', () => {
    expect(component).toBeTruthy();
  });
});
