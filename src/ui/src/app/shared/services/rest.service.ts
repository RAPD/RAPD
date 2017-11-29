import { Injectable } from '@angular/core';
import { Headers,
         Response } from '@angular/http';

import { Observable } from 'rxjs/Observable';
import { Subscriber } from 'rxjs/Subscriber';
import { AuthHttp } from 'angular2-jwt';
import * as moment from 'moment-mini';

import { GlobalsService } from './globals.service';

import { User } from '../classes/user';
import { Group } from '../classes/group';
import { Session } from '../classes/session';
import { Project } from '../classes/project';
import { Image } from '../classes/image';
import { Run } from '../classes/run';

@Injectable()
export class RestService {

  constructor(private globals_service: GlobalsService,
              private authHttp: AuthHttp) { }

  //
  // USERS
  //
  public getUsers(): Observable<User[]> {

    console.log('getUsers');

    let header = new Headers();
    header.append('Content-Type', 'application/json');

    return this.authHttp.get(this.globals_service.site.restApiUrl + '/users')
      .map(this.extractUsers)
      .catch(error => this.handleError(error));
  }

  private extractUsers(res: Response, error) {
    let body = res.json();
    return body.users || [];
  }

  // Submit a user to be saved in the database
  public submitUser(user: User): Observable<any> {

    console.log('submitUser', user);
    console.log(this.globals_service.site.restApiUrl + 'users/' + user._id);

    let header = new Headers();
    header.append('Content-Type', 'application/json');

    return this.authHttp.put(
      this.globals_service.site.restApiUrl + '/users/' + user._id,
      JSON.stringify({user: user}),
      {headers: header}
    )
    // .map(res => res.json())
    .catch(error => this.handleError(error));
  }

  // Delete a user from the database
  public deleteUser(_id: string): Observable<any> {

    console.log('deleteUser', _id);

    return this.authHttp.delete(this.globals_service.site.restApiUrl + 'users/' + _id).map(res => res.json());
  }

  public getGroups(): Observable<Group[]> {

    console.log('getGroups');

    return this.authHttp.get(this.globals_service.site.restApiUrl + 'groups')
      .map(this.extractGroups)
      .catch(error => this.handleError(error));
  }

  //
  // GROUPS
  //
  private extractGroups(res: Response, error) {

    // console.log('error', error);
    let body = res.json();

    // for (let user of body) {
    //   // console.log(session);
    //   session.start_display = moment(session.start).format('YYYY-MM-DD hh:mm:ss');
    //   session.end_display = moment(session.end).format('YYYY-MM-DD hh:mm:ss');
    // }
    return body.groups || [];
  }

  // Submit a group to be saved in the database
  public submitGroup(group: Group): Observable<any> {

    console.log('submitGroup');

    let header = new Headers();
    header.append('Content-Type', 'application/json'); // 'application/x-www-form-urlencoded'

    return this.authHttp.put(
      this.globals_service.site.restApiUrl + 'groups/' + group._id,
      JSON.stringify({group: group}),
      {headers: header}
    );
    // .map(res => res.json());
  }

  // Delete a group from the database
  public deleteGroup(_id: string): Observable<any> {

    console.log('deleteGroup', _id);

    return this.authHttp.delete(this.globals_service.site.restApiUrl + 'groups/' + _id); //.map(res => res.json());
  }

  //
  // SESSIONS
  //
  public getSessions(): Observable<Session[]> {
    // console.log('getSessions');
    return this.authHttp.get(this.globals_service.site.restApiUrl + 'sessions')
      .map(this.extractSessions)
      .catch(error => this.handleError(error));
  }

  private extractSessions(res: Response, error) {
    // console.error(error);
    let body = res.json();
    return body.sessions || [];
  }

  // Submit a session to be saved in the database
  public submitSession(session: Session): Observable<any> {

    console.log('submitSession');

    let header = new Headers();
    header.append('Content-Type', 'application/json'); // 'application/x-www-form-urlencoded'

    return this.authHttp.put(
      this.globals_service.site.restApiUrl + 'sessions/' + session._id,
      JSON.stringify({session: session}),
      {headers: header}
    );
    // .map(res => res.json());
  }

  // Delete a user from the database
  public deleteSession(_id: string): Observable<any> {

    console.log('deleteSession', _id);

    return this.authHttp.delete(this.globals_service.site.restApiUrl + 'sessions/' + _id); //.map(res => res.json());
  }

  //
  // IMAGES
  //
  public getImageData(_id:string): Observable<Image> {

    console.log('getImageData _id:', _id);

    return this.authHttp.get(this.globals_service.site.restApiUrl + 'images/' + _id);
                        // .map(res => res.json());
  }

  // RUN methods
  public getRunData(_id:string): Observable<Run> {

    console.log('getRunData _id:', _id);

    return this.authHttp.get(this.globals_service.site.restApiUrl + 'runs/' + _id)
                        .map(res => res.json().run)
                        .catch(error => this.handleError(error));
  }

  //
  // PROJECT methods
  //
  public getProjects(): Observable<Project[]> {

    console.log('getProjects');

    return this.authHttp.get(this.globals_service.site.restApiUrl + 'projects')
      .map(res => res.json().projects)
      .catch(error => this.handleError(error));
  }

  public submitProject(project: Project): Observable<any> {

    console.log('submitProject', project);
    console.log(this.globals_service.site.restApiUrl + 'projects/' + project._id);

    let header: Headers = new Headers();
    header.append('Content-Type', 'application/json');

    return this.authHttp.put(
      this.globals_service.site.restApiUrl + 'projects/' + project._id,
      JSON.stringify({project:project}),
      {headers:header}
    )
    // .map(res => res.json())
    .catch(error => this.handleError(error));
  }

  // Delete a project from the database
  public deleteProject(_id: string): Observable<any> {

    console.log('deleteProject', _id);

    return this.authHttp.delete(
      this.globals_service.site.restApiUrl + 'projects/' + _id
    )
    // .map(res => res.json())
    .catch(error => this.handleError(error));
  }

  public addResultToProject(data:any): Observable<any> {

    console.log('addResultToProject');

    let header: Headers = new Headers();
    header.append('Content-Type', 'application/json');

    return this.authHttp.put(
      this.globals_service.site.restApiUrl + 'projects/add_result',
      JSON.stringify({
        project_id:data._id,
        result:data.result
      }),
      {headers:header}
    )
    // .map(res => res.json())
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
      this.globals_service.site.restApiUrl + 'jobs/submit',
      JSON.stringify({request:request}),
      {headers:header}
    )
    // .map(res => res.json())
    .catch(error => this.handleError(error));
  }

  //
  // OVERWATCH methods
  //
  public getOverwatches(): Observable<any> {

    // console.log('getOverwatches');

    return this.authHttp.get(this.globals_service.site.restApiUrl + '/overwatches')
                        .map(res => res.json())
                        .catch(error => this.handleError(error));
  }

  public stopOverwatch(id:string) {

    let header: Headers = new Headers();
    header.append('Content-Type', 'application/json');

    return this.authHttp.put(
      this.globals_service.site.restApiUrl + 'overwatches/stop/' + id,
      JSON.stringify({id:id}),
      {headers:header}
    )
    .map(res => res.json())
    .catch(error => this.handleError(error));
  }

  public stopAllOverwatches() {

    // console.log('stopAllOverwatches');

    let header: Headers = new Headers();
    header.append('Content-Type', 'application/json');

    return this.authHttp.put(
      this.globals_service.site.restApiUrl + 'overwatches/stopall',
      JSON.stringify({id:'foo'}),
      {headers:header}
    )
    .map(res => res.json())
    .catch(error => this.handleError(error));
  }

  public startOverwatch(id:string) {

    let header: Headers = new Headers();
    header.append('Content-Type', 'application/json');

    return this.authHttp.put(
      this.globals_service.site.restApiUrl + 'overwatches/start/' + id,
      JSON.stringify({id:id}),
      {headers:header}
    )
    .map(res => res.json())
    .catch(error => this.handleError(error));
  }

  //
  // DASHBOARD METHODS
  //
  public getDashboardResults(): Observable<any> {

    // console.log('getDashboardResults');

    return this.authHttp.get(this.globals_service.site.restApiUrl + 'dashboard/results')
                        .map(res => res.json())
                        .catch(error => this.handleError(error));
  }

  public getDashboardLogins(): Observable<any> {

    // console.log('getDashboardLogins');

    return this.authHttp.get(this.globals_service.site.restApiUrl + 'dashboard/logins')
                        .map(res => res.json())
                        .catch(error => this.handleError(error));
  }

  public getServerActivities(): Observable<any> {

    // console.log('getServerActivities');

    return this.authHttp.get(this.globals_service.site.restApiUrl + 'dashboard/server_activities')
                        .map(res => res.json())
                        .catch(error => this.handleError(error));
  }

  // Request a download
  public getDownloadById(id): Observable<any> {

    console.log('getDownload', id)

    return this.authHttp.get(this.globals_service.site.restApiUrl + 'download_by_id/' + id)
                        .map(res => {
                          // console.log(res);
                          if (res.status === 200) {
                            // console.log('length', res._body.length);
                            // convert base64 string to byte array
                            var byteCharacters = atob((<any>res)._body);
                            var byteNumbers = new Array(byteCharacters.length);
                            for (var i = 0; i < byteCharacters.length; i++){
                                byteNumbers[i] = byteCharacters.charCodeAt(i);
                            }
                            var byteArray = new Uint8Array(byteNumbers);
                            // console.log(byteArray);
                            var blob = new Blob([byteArray], {type:'application/octet-stream'});
                            // console.log(blob);
                            var url= window.URL.createObjectURL(blob);
                            // console.log(url);
                            // window.open(url);
                            // window.open("data:text/plain;charset=ISO-8859-1;"+res._body,);
                            var pom = document.createElement('a');
                            pom.setAttribute('href', url);
                            pom.setAttribute('download', "foobar.tar.bz2");

                            if (document.createEvent) {
                                var event = document.createEvent('MouseEvents');
                                event.initEvent('click', true, true);
                                pom.dispatchEvent(event);
                            }
                            else {
                                pom.click();
                            }
                          }
                          return res.json();
                        })
                        .catch(error => this.handleError(error));
  }


  // Generic error handler for connection problems
  private handleError(error) {
    return Observable.of({
      success:false,
      message:error.toString()
    });
  }

}
