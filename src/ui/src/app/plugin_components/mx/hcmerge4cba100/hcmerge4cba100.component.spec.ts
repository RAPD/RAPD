import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { Hcmerge4cba100Component } from './hcmerge4cba100.component';

describe('Hcmerge4cba100Component', () => {
  let component: Hcmerge4cba100Component;
  let fixture: ComponentFixture<Hcmerge4cba100Component>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ Hcmerge4cba100Component ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(Hcmerge4cba100Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
