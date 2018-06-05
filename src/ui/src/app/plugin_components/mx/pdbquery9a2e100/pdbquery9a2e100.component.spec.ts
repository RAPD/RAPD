import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { Pdbquery9a2e100Component } from './pdbquery9a2e100.component';

describe('Pdbquery9a2e100Component', () => {
  let component: Pdbquery9a2e100Component;
  let fixture: ComponentFixture<Pdbquery9a2e100Component>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ Pdbquery9a2e100Component ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(Pdbquery9a2e100Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
