import { Injectable } from '@angular/core';
import { Response } from '@angular/http';

import { Observable } from 'rxjs/Observable';
import { HttpClient,
         HttpParams,
         HttpHeaders } from '@angular/common/http';

import { GlobalsService } from './globals.service';

import { Session } from '../classes/session';

@Injectable()
export class SessionService {

  constructor(private globalsService: GlobalsService,
              public authHttp: HttpClient) { }

  getSessions(): Observable<Session[]> {

    // console.log('getSessions');

    return this.authHttp.get(this.globalsService.site.restApiUrl + '/sessions')
      .map(this.extractData);
      // .catch(this.handleError);
  }

  // New version of fetching sessions for MaterialDesign table
  findSessions(_id = '',
               filter = '',
               sortOrder = 'asc',
               pageNumber = 0,
               pageSize = 3): Observable<Session[]> {

    // console.log('findSessions');
    return this.authHttp.get(this.globalsService.site.restApiUrl + '/sessions2', {
      params: new HttpParams()
      .set('_id', _id.toString())
      .set('filter', filter)
      .set('sortOrder', sortOrder)
      .set('pageNumber', pageNumber.toString())
      .set('pageSize', pageSize.toString()),
    })
    .map(this.extractData);
  }

  findDocuments(
    query:any={},
    sortKey:string='',
    sortOrder:string='asc',
    skip:number=0,
    limit:number=20,): Observable<Session[]> {

    // Construct data to post to server
    const headers = new HttpHeaders();
    headers.append('Content-Type', 'application/json');
    const submit1 = {
      "limit": limit,
      "skip": skip,
      "sortKey": sortKey,
      "sortOrder": sortOrder,
    };
    const finalSubmit = {...submit1, ...query}

    return this.authHttp.post<any[]>(
      this.globalsService.site.restApiUrl+"sessions/search",
      finalSubmit,
      {headers});
  }

  countDocuments(query:any): Observable<number> {
    const headers = new HttpHeaders();
    headers.append('Content-Type', 'application/json');

    const submit1 = {"count": true};
    const finalSubmit = {...submit1, ...query}

    return this.authHttp.post<number>(
      this.globalsService.site.restApiUrl+"sessions/search",
      finalSubmit,
      {headers});
  }

  private extractData(res: Response, error) {
    // console.log('error', error);
    const body = res.json();
    // for (let session of body) {
    //   console.log(session);
    //   session.start_display = moment(session.timestamp).format('YYYY-MM-DD hh:mm:ss');
    //   session.end_display = moment(session.last_process).format('YYYY-MM-DD hh:mm:ss');
    // }
    return body || {};
  }

  // private handleError(error: any) {
  //   console.error('An error occurred', error);
  //   return Observable.throw(error.message || error);
  // }

}
