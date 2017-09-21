import { Injectable } from '@angular/core';
import { Headers, Response } from '@angular/http';

import { Observable } from 'rxjs/Observable';
import { Subscriber } from 'rxjs/Subscriber';
import { AuthHttp } from 'angular2-jwt';
import * as moment from 'moment';

import { User } from '../classes/user';
import { Group } from '../classes/group';
import { Session } from '../classes/session';
import { Project } from '../classes/project';
import { Image } from '../classes/image';
import { Run } from '../classes/run';

@Injectable()
export class RestService {

  private apiUrl = 'http://localhost:3000/api';

  constructor(private authHttp: AuthHttp) { }

  public getUsers(): Observable<User[]> {

    console.log('getUsers');

    return this.authHttp.get(this.apiUrl + '/users')
      .map(this.extractUsers);
      // .catch(this.handleError);
  }

  private extractUsers(res: Response, error) {
    console.log('error', error);
    let body = res.json();
    console.log(body);
    return body || {};
  }

  // Submit a user to be saved in the database
  public submitUser(user: User): Observable<any> {

    console.log('submitUser');

    let header = new Headers();
    header.append('Content-Type', 'application/json'); // 'application/x-www-form-urlencoded'

    return this.authHttp.put(
      this.apiUrl + '/users/' + user._id,
      JSON.stringify({user: user}),
      {headers: header}
    )
    .map(res => res.json());
    // .subscribe(
    //   data => console.log(data),
    //   err => console.log(err),
    //   () => console.log('Request Complete')
    // );
  }

  // Delete a user from the database
  public deleteUser(_id: string): Observable<any> {

    console.log('deleteUser', _id);

    return this.authHttp.delete(this.apiUrl + '/users/' + _id).map(res => res.json());
  }

  public getGroups(): Observable<Group[]> {

    console.log('getGroups');

    return this.authHttp.get(this.apiUrl + '/groups')
      .map(this.extractGroups);
      // .catch(this.handleError);
  }

  private extractGroups(res: Response, error) {

    // console.log('error', error);
    let body = res.json();

    // for (let user of body) {
    //   // console.log(session);
    //   session.start_display = moment(session.start).format('YYYY-MM-DD hh:mm:ss');
    //   session.end_display = moment(session.end).format('YYYY-MM-DD hh:mm:ss');
    // }
    return body || {};
  }

  // Submit a group to be saved in the database
  public submitGroup(group: Group): Observable<any> {

    console.log('submitGroup');

    let header = new Headers();
    header.append('Content-Type', 'application/json'); // 'application/x-www-form-urlencoded'

    return this.authHttp.put(
      this.apiUrl + '/groups/' + group._id,
      JSON.stringify({group: group}),
      {headers: header}
    )
    .map(res => res.json());
  }

  // Delete a user from the database
  public deleteGroup(_id: string): Observable<any> {

    console.log('deleteGroup', _id);

    return this.authHttp.delete(this.apiUrl + '/groups/' + _id).map(res => res.json());
  }

  public getSessions(): Observable<Session[]> {

    // console.log('getSessions');

    return this.authHttp.get(this.apiUrl + '/sessions')
      .map(this.extractSessions);
      // .catch(this.handleError);
  }

  private extractSessions(res: Response, error) {

    // console.log('error', error);
    let body = res.json();

    for (let session of body) {
      // console.log(session);
      session.start_display = moment(session.start).format('YYYY-MM-DD hh:mm:ss');
      session.end_display = moment(session.end).format('YYYY-MM-DD hh:mm:ss');
    }
    return body || {};
  }

  // Submit a session to be saved in the database
  public submitSession(session: Session): Observable<any> {

    console.log('submitSession');

    let header = new Headers();
    header.append('Content-Type', 'application/json'); // 'application/x-www-form-urlencoded'

    return this.authHttp.put(
      this.apiUrl + '/sessions/' + session._id,
      JSON.stringify({session: session}),
      {headers: header}
    )
    .map(res => res.json());
  }

  // IMAGE methods
  public getImageData(_id:string): Observable<Image> {

    console.log('getImageData _id:', _id);

    return this.authHttp.get(this.apiUrl + '/images/' + _id)
                        .map(res => res.json());
  }

  // RUN methods
  public getRunData(_id:string): Observable<Run> {

    console.log('getRunData _id:', _id);

    return this.authHttp.get(this.apiUrl + '/runs/' + _id)
                        .map(res => res.json());
  }


  //
  // PROJECT methods
  //
  public getProjects(): Observable<Project[]> {

    console.log('getProjects');

    return this.authHttp.get(this.apiUrl + '/projects')
      .map(res => res.json())
      .catch(error => this.handleError(error));
  }

  public newProject(project): Observable<any> {

    console.log('newProject');

    let header: Headers = new Headers();
    header.append('Content-Type', 'application/json');

    return this.authHttp.put(
      this.apiUrl + '/projects',
      JSON.stringify({project:project}),
      {headers:header}
    )
    .map(res => res.json())
    .catch(error => this.handleError(error));
  }

  public addResultToProject(data:any): Observable<any> {

    console.log('addResultToProject');

    let header: Headers = new Headers();
    header.append('Content-Type', 'application/json');

    return this.authHttp.put(
      this.apiUrl + '/projects/add_result',
      JSON.stringify({
        project_id:data._id,
        result:data.result
      }),
      {headers:header}
    )
    .map(res => res.json())
    .catch(error => this.handleError(error));
  }

  //
  // JOB methods
  //
  public submitJob(request:any): Observable<any>{

    // console.log('submitJob', request);

    let header = new Headers();
    header.append('Content-Type', 'application/json'); // 'application/x-www-form-urlencoded'

    return this.authHttp.put(
      this.apiUrl + '/requests',
      JSON.stringify({request:request}),
      {headers:header}
    )
    .map(res => res.json())
    .catch(error => this.handleError(error));
  }

  // Generic error handler for connection problems
  private handleError(error) {
    return Observable.of({
      success:false,
      error:error
    });
  }

}
