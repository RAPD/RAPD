import { Injectable } from '@angular/core';
import { Headers,
         Response } from '@angular/http';

import { Observable } from 'rxjs/Observable';
import { AuthHttp } from 'angular2-jwt';
import { GlobalsService } from './globals.service';

@Injectable()
export class RequestsService {

  constructor(private globals_service: GlobalsService,
              private authHttp: AuthHttp) { }

  public submitRequest(request: any): Observable<any> {

    console.log('submitRequest');
    console.log(this.globals_service.apiUrl);
    console.log(request);

    let header = new Headers();
    header.append('Content-Type', 'application/json');

    return this.authHttp.put(
      this.globals_service.apiUrl + '/requests',
      JSON.stringify({request:request}),
      {headers:header}
    )
    .map(res => res.json());
  }

}
