import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ReindexDialogComponent } from './reindex-dialog.component';

describe('ReindexDialogComponent', () => {
  let component: ReindexDialogComponent;
  let fixture: ComponentFixture<ReindexDialogComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ReindexDialogComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ReindexDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should be created', () => {
    expect(component).toBeTruthy();
  });
});
