import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MaintoolbarComponent } from './maintoolbar.component';

describe('MaintoolbarComponent', () => {
  let component: MaintoolbarComponent;
  let fixture: ComponentFixture<MaintoolbarComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [MaintoolbarComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(MaintoolbarComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
