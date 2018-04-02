/* tslint:disable:no-unused-variable */

import { TestBed, async, inject } from '@angular/core/testing';
import { RestService } from './rest.service';

describe('Service: Admin', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [RestService]
    });
  });

  it('should ...', inject([RestService], (service: RestService) => {
    expect(service).toBeTruthy();
  }));
});
