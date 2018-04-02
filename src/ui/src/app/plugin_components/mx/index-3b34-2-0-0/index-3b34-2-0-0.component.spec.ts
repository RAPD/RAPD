import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { Index3b34200Component } from './index-3b34-2-0-0.component';

describe('Index3b34200Component', () => {
  let component: Index3b34200Component;
  let fixture: ComponentFixture<Index3b34200Component>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ Index3b34200Component ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(Index3b34200Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should be created', () => {
    expect(component).toBeTruthy();
  });
});
