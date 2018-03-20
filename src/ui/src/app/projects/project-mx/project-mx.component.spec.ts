import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ProjectMxComponent } from './project-mx.component';

describe('ProjectMxComponent', () => {
  let component: ProjectMxComponent;
  let fixture: ComponentFixture<ProjectMxComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ProjectMxComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ProjectMxComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
