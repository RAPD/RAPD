import { Injectable } from '@angular/core';
import { Headers,
         Response } from '@angular/http';

import { Observable } from 'rxjs/Observable';
import { HttpClient,
         HttpHeaders } from '@angular/common/http';

import { GlobalsService } from './globals.service';

@Injectable()
export class RequestsService {

  constructor(private globals_service: GlobalsService,
              private authHttp: HttpClient) { }

  public submitRequest(request: any): Observable<any> {

    console.log('submitRequest');
    console.log(this.globals_service.site.restApiUrl);
    console.log(request);

    let header = new HttpHeaders();
    header.append('Content-Type', 'application/json');

    return this.authHttp.put(
      this.globals_service.site.restApiUrl + '/requests',
      JSON.stringify({request:request}),
      {headers:header}
    );
    // .map(res => res.json());
  }

}
