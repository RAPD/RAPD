import { TestBed } from '@angular/core/testing';

import { Sessions.Datasource } from './sessions.datasource';

describe('Sessions.Datasource', () => {
  let service: Sessions.Datasource;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(Sessions.Datasource);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
