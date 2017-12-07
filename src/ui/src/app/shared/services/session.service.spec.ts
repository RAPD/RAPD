/* tslint:disable:no-unused-variable */

import { addProviders, async, inject } from '@angular/core/testing';
import { SessionService } from './session.service';

describe('Service: Session', () => {
  beforeEach(() => {
    addProviders([SessionService]);
  });

  it('should ...',
    inject([SessionService],
      (service: SessionService) => {
        expect(service).toBeTruthy();
      }));
});
