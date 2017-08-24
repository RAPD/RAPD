import { async,
         ComponentFixture,
         TestBed } from '@angular/core/testing';

// import { PlotOmegaStartComponent } from './plot-omega-start.component';

describe('PlotOmegaStartComponent', () => {
  let component: PlotOmegaStartComponent;
  let fixture: ComponentFixture<PlotOmegaStartComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PlotOmegaStartComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PlotOmegaStartComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should be created', () => {
    expect(component).toBeTruthy();
  });
});
