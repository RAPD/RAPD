import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { MxImageComponent } from './mx-image.component';

describe('MxImageComponent', () => {
  let component: MxImageComponent;
  let fixture: ComponentFixture<MxImageComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ MxImageComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MxImageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
