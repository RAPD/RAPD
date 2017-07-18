/* tslint:disable:no-unused-variable */

import { addProviders, async, inject } from '@angular/core/testing';
import { ResultsService } from './results.service';

describe('Service: Results', () => {
  beforeEach(() => {
    addProviders([ResultsService]);
  });

  it('should ...',
    inject([ResultsService],
      (service: ResultsService) => {
        expect(service).toBeTruthy();
      }));
});
