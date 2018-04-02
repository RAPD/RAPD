/* tslint:disable:no-unused-variable */

import { addProviders, async, inject } from '@angular/core/testing';
import { WebsocketService } from './websocket.service';

describe('Service: Results', () => {
  beforeEach(() => {
    addProviders([WebsocketService]);
  });

  it('should ...',
    inject([WebsocketService],
      (service: WebsocketService) => {
        expect(service).toBeTruthy();
      }));
});
