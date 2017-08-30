import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { IntegrateBd11200Component } from './integrate-bd11-2-0-0.component';

describe('IntegrateBd11200Component', () => {
  let component: IntegrateBd11200Component;
  let fixture: ComponentFixture<IntegrateBd11200Component>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ IntegrateBd11200Component ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(IntegrateBd11200Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should be created', () => {
    expect(component).toBeTruthy();
  });
});
