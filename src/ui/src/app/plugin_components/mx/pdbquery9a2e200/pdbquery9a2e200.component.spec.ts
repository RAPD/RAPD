import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { Pdbquery9a2e200Component } from './pdbquery9a2e200.component';

describe('Pdbquery9a2e200Component', () => {
  let component: Pdbquery9a2e200Component;
  let fixture: ComponentFixture<Pdbquery9a2e200Component>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ Pdbquery9a2e200Component ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(Pdbquery9a2e200Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
