import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { Mrc33b200Component } from './mrc33b200.component';

describe('Mrc33b200Component', () => {
  let component: Mrc33b200Component;
  let fixture: ComponentFixture<Mrc33b200Component>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ Mrc33b200Component ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(Mrc33b200Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
