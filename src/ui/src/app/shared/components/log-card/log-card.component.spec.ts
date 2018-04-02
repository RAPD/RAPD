import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { LogCardComponent } from './log-card.component';

describe('LogCardComponent', () => {
  let component: LogCardComponent;
  let fixture: ComponentFixture<LogCardComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ LogCardComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(LogCardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
