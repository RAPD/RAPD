import { HttpClient, HttpHeaders } from "@angular/common/http";
import { Injectable } from "@angular/core";
// import { Headers, Response } from "@angular/http";
import { Observable } from "rxjs/Observable";
import { Subscriber } from "rxjs/Subscriber";
// import * as moment from "moment-mini";

import { GlobalsService } from "./globals.service";

import { Group } from "../classes/group";
import { Image } from "../classes/image";
import { Project } from "../classes/project";
import { Run } from "../classes/run";
import { Session } from "../classes/session";
import { User } from "../classes/user";

function baseName(str: string): string {
  var base = new String(str).substring(str.lastIndexOf("/") + 1);
  if (base.lastIndexOf(".") != -1)
    base = base.substring(0, base.lastIndexOf("."));
  return base;
}

@Injectable()
export class RestService {
  constructor(
    private globals_service: GlobalsService,
    private authHttp: HttpClient
  ) {}

  //
  // DASHBOARD METHODS
  //
  public getDashboardResults(): Observable<any> {
    // console.log('getDashboardResults');

    return (
      this.authHttp
        .get(this.globals_service.site.restApiUrl + "/dashboard/results")
        // .map(res => res.json())
        .catch(error => this.handleError(error))
    );
  }

  public getDashboardLogins(): Observable<any> {
    // console.log('getDashboardLogins');

    return (
      this.authHttp
        .get(this.globals_service.site.restApiUrl + "/dashboard/logins")
        // .map(res => res.json())
        .catch(error => this.handleError(error))
    );
  }

  public getServerActivities(): Observable<any> {
    // console.log('getServerActivities');

    return (
      this.authHttp
        .get(
          this.globals_service.site.restApiUrl + "/dashboard/server_activities"
        )
        // .map(res => res.json())
        .catch(error => this.handleError(error))
    );
  }

  //
  // DOWNLOAD METHODS
  //

  // Request a download
  public getDownloadById(id: string, filename: string): void {
    console.log("getDownloadById", id, filename);

    this.authHttp
      .get(this.globals_service.site.restApiUrl + "/download_by_id/" + id, {
        responseType: "text"
      })
      .subscribe(res => {
        // Convert base64 string to byte array
        var byteCharacters = atob(<any>res);
        var byteNumbers = new Array(byteCharacters.length);
        for (var i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        var byteArray = new Uint8Array(byteNumbers);
        // Convert byte array to Blob
        var blob = new Blob([byteArray], {
          type: "application/octet-stream"
        });
        // Create ObjectURL
        var url = window.URL.createObjectURL(blob);
        // Create DOM element with download attribute
        var pom = document.createElement("a");
        pom.setAttribute("href", url);
        pom.setAttribute("download", filename);
        // Now trigger download
        if (document.createEvent) {
          var event = document.createEvent("MouseEvents");
          event.initEvent("click", true, true);
          pom.dispatchEvent(event);
        } else {
          pom.click();
        }
      });
  }

  public getDownloadByHash(hash: string, filename: string): void {
    console.log("getDownloadByHash", hash, filename);

    // Get the base filename
    filename = baseName(filename);

    this.authHttp
      .get(this.globals_service.site.restApiUrl + "/download_by_hash/" + hash, {
        responseType: "text"
      })
      .subscribe(res => {
        // Convert base64 string to byte array
        var byteCharacters = atob(res);
        var byteNumbers = new Array(byteCharacters.length);
        for (var i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        var byteArray = new Uint8Array(byteNumbers);
        // Convert byte array to Blob
        var blob = new Blob([byteArray], {
          type: "application/octet-stream"
        });
        // Create ObjectURL
        var url = window.URL.createObjectURL(blob);
        // Create DOM element with download attribute
        var pom = document.createElement("a");
        pom.setAttribute("href", url);
        pom.setAttribute("download", filename);
        // Now trigger download
        if (document.createEvent) {
          var event = document.createEvent("MouseEvents");
          event.initEvent("click", true, true);
          pom.dispatchEvent(event);
        } else {
          pom.click();
        }
      });
  }

  //
  // UglyMol Methods
  //
  public getPdbByHash(hash: string, filename: string) {

    console.log("getPdbByHash", hash);

    this.authHttp
      .get(this.globals_service.site.restApiUrl + "/get_pdb_by_hash/" + hash, {
        responseType: "text",
      }).subscribe(res => {
        console.log(res);
      });
  }

  public getPdb(pdbFile: string) {
    console.log("getPdb", pdbFile);

    return (this.authHttp
      .get(this.globals_service.site.restApiUrl + "/download_pdb/" + pdbFile, {
        responseType: "text"
      }));
      // .subscribe(res => {
      //   console.log(res);
      // });
  }

  public getMap(mapFile: string) {
    console.log("getMap", mapFile);

    return (this.authHttp
      .get(this.globals_service.site.restApiUrl + "/download_map/" + mapFile, {
        responseType: "arraybuffer",
      }));
      // .subscribe(res => {
      //   console.log(res);
      // });
  }

  //
  // GROUP METHODS
  //
  public extractGroups(res, error) {
    // console.log('error', error);
    // let body = res.json();

    // Sort alphabetically by surname, if possible
    // res.groups.sort((g1, g2) => {
    //   var s1 = g1.groupname.split(" ")[g1.groupname.split(" ").length - 1];
    //   var s2 = g2.groupname.split(" ")[g1.groupname.split(" ").length - 1];
    //   if (s1 > s2) {
    //     return 1;
    //   }
    //   if (s1 < s2) {
    //     return -1;
    //   }
    //   return 0;
    // });

    return res.groups || [];
  }

  // Submit a group to be saved in the database
  public submitGroup(group: Group): Observable<any> {
    console.log("submitGroup");

    let header = new HttpHeaders();
    header.append("Content-Type", "application/json"); // 'application/x-www-form-urlencoded'

    return (
      this.authHttp
        .put(
          this.globals_service.site.restApiUrl + "/groups/" + group._id,
          JSON.stringify({ group: group })
          // { headers: header }
        )
        // .map(res => res.json())
        .catch(error => this.handleError(error))
    );
  }

  // Delete a group from the database
  public deleteGroup(_id: string): Observable<any> {
    console.log("deleteGroup", _id);

    return this.authHttp.delete(
      this.globals_service.site.restApiUrl + "/groups/" + _id
    ); //.map(res => res.json());
  }

  // Call to populate groups from LDAP server
  public populateGroups(): Observable<any> {
    return (
      this.authHttp
        .get(this.globals_service.site.restApiUrl + "/groups/populate")
        // .map(res => res.json())
        .catch(error => this.handleError(error))
    );
  }

  //
  // IMAGE METHODS
  //
  public getImageData(_id: string): Observable<Image> {
    console.log("getImageData _id:", _id);

    return this.authHttp.get(
      this.globals_service.site.restApiUrl + "/images/" + _id
    );
    // .map(res => res.json());
  }

  public getImageJpeg(request: any): Observable<any> {
    // console.log('getImageJpeg', request);

    const req = JSON.stringify(request);
    // console.log(req);

    return this.authHttp
      .get(this.globals_service.site.restApiUrl + "/image_jpeg/" + req)
      .map(res => {
        console.log(res);
        // return res.json();
      })
      .catch(error => this.handleError(error));
  }

  //
  // JOB methods
  //
  public submitJob(request: any): Observable<any> {
    // console.log('submitJob', request);

    const header = new HttpHeaders();
    header.append("Content-Type", "application/json"); // 'application/x-www-form-urlencoded'

    return (
      this.authHttp
        .put(
          this.globals_service.site.restApiUrl + "/jobs/submit",
          JSON.stringify({ request })
          // { headers: header }
        )
        // .map(res => res.json())
        .catch(error => this.handleError(error))
    );
  }

  //
  // OVERWATCH methods
  //
  public getOverwatches(): Observable<any> {
    // console.log('getOverwatches');

    return (
      this.authHttp
        .get(this.globals_service.site.restApiUrl + "/overwatches")
        // .map(res => res.json())
        .catch(error => this.handleError(error))
    );
  }

  public stopOverwatch(id: string) {
    let header = new HttpHeaders();
    header.append("Content-Type", "application/json");

    return (
      this.authHttp
        .put(
          this.globals_service.site.restApiUrl + "/overwatches/stop/" + id,
          JSON.stringify({ id: id })
          // { headers: header }
        )
        // .map(res => res.json())
        .catch(error => this.handleError(error))
    );
  }

  public stopAllOverwatches() {
    // console.log('stopAllOverwatches');

    let header = new HttpHeaders();
    header.append("Content-Type", "application/json");

    return (
      this.authHttp
        .put(
          this.globals_service.site.restApiUrl + "/overwatches/stopall",
          JSON.stringify({ id: "foo" })
          // { headers: header }
        )
        // .map(res => res.json())
        .catch(error => this.handleError(error))
    );
  }

  public startOverwatch(id: string) {
    let header = new HttpHeaders();
    header.append("Content-Type", "application/json");

    return (
      this.authHttp
        .put(
          this.globals_service.site.restApiUrl + "/overwatches/start/" + id,
          JSON.stringify({ id: id })
          // { headers: header }
        )
        // .map(res => res.json())
        .catch(error => this.handleError(error))
    );
  }

  //
  // PDB Methods
  //
  public getUploadedPdbsBySession(id: string): Observable<any> {
    console.log("getUploadedPdbsBySession", id);

    return this.authHttp
      .get(this.globals_service.site.restApiUrl + "/pdbs/by_session/" + id)
      .catch(error => this.handleError(error));
  }

  //
  // PROJECT methods
  //
  public getProjects(): Observable<any> {
    // TODO :Observable<Project[]> {
    console.log("getProjects");

    return this.authHttp
      .get(this.globals_service.site.restApiUrl + "/projects")
      .catch(error => this.handleError(error));
  }

  public getProjectsBySession(id: string): Observable<any> {
    console.log("getProjectsBySession", id);

    return this.authHttp
      .get(this.globals_service.site.restApiUrl + "/projects/by_session/" + id)
      .catch(error => this.handleError(error));
  }

  public getProject(id: string): Observable<any> {
    console.log("getProject", id);

    return (
      this.authHttp
        .get(this.globals_service.site.restApiUrl + "/projects/" + id)
        // .map(res => res.json())
        .catch(error => this.handleError(error))
    );
  }

  public submitProject(project: Project): Observable<any> {
    console.log("submitProject", project);
    console.log(
      this.globals_service.site.restApiUrl + "/projects/" + project._id
    );

    let header = new HttpHeaders();
    header.append("Content-Type", "application/json");

    return (
      this.authHttp
        .put(
          this.globals_service.site.restApiUrl + "/projects/" + project._id,
          JSON.stringify({ project: project })
          // { headers: header }
        )
        // .map(res => res.json())
        .catch(error => this.handleError(error))
    );
  }

  // Delete a project from the database
  public deleteProject(_id: string): Observable<any> {
    console.log("deleteProject", _id);

    return (
      this.authHttp
        .delete(this.globals_service.site.restApiUrl + "/projects/" + _id)
        // .map(res => res.json())
        .catch(error => this.handleError(error))
    );
  }

  public addResultToProject(data: any): Observable<any> {
    console.log("addResultToProject");

    let header = new HttpHeaders();
    header.append("Content-Type", "application/json");

    return (
      this.authHttp
        .put(
          this.globals_service.site.restApiUrl + "/projects_add_result",
          JSON.stringify({
            project_id: data._id,
            result: data.result
          })
          // { headers: header }
        )
        // .map(res => res.json())
        .catch(error => this.handleError(error))
    );
  }

  //
  // RESULT METHODS
  //
  public getResult(_id: string): Observable<any> {
    return (
      this.authHttp
        .get(this.globals_service.site.restApiUrl + "/results/" + _id)
        // .map(res => res.json())
        .catch(error => this.handleError(error))
    );
  }

  public getResultDetail(_id: string): Observable<any> {
    console.log("getResultDetail", _id);

    return (
      this.authHttp
        .get(this.globals_service.site.restApiUrl + "/result_details/" + _id)
        // .map(res => res.json())
        .catch(error => this.handleError(error))
    );
  }

  //
  // RUN methods
  //
  public getRunData(_id: string): Observable<Run> {
    // console.log('getRunData _id:', _id);

    return (
      this.authHttp
        .get(this.globals_service.site.restApiUrl + "/runs/" + _id)
        // .map(res => res.run)
        .catch(error => this.handleError(error))
    );
  }

  //
  // SESSIONS
  //
  public getSessions(): Observable<Session[]> {
    console.log("getSessions");
    return this.authHttp
      .get(this.globals_service.site.restApiUrl + "/sessions")
      .map(this.extractSessions)
      .catch(error => this.handleError(error));
  }

  private extractSessions(res, error) {
    // console.error(res);
    // let body = res.json();
    return res.sessions || [];
  }

  // Submit a session to be saved in the database
  public submitSession(session: Session): Observable<any> {
    console.log("submitSession");

    let header = new HttpHeaders();
    header.append("Content-Type", "application/json"); // 'application/x-www-form-urlencoded'

    return (
      this.authHttp
        .put(
          this.globals_service.site.restApiUrl + "/sessions/" + session._id,
          JSON.stringify({ session: session })
          // { headers: header }
        )
        // .map(res => res.json())
        .catch(error => this.handleError(error))
    );
  }

  // Delete a user from the database
  public deleteSession(_id: string): Observable<any> {
    console.log("deleteSession", _id);

    return this.authHttp.delete(
      this.globals_service.site.restApiUrl + "/sessions/" + _id
    ); //.map(res => res.json());
  }

  //
  // USERS
  //
  public getUsers(): Observable<User[]> {
    console.log("getUsers");

    // let header = new HttpHeaders();
    // header.append("Content-Type", "application/json");

    return this.authHttp
      .get(this.globals_service.site.restApiUrl + "/users")
      .map(this.extractUsers)
      .catch(error => this.handleError(error));
  }

  private extractUsers(res, error) {
    return res.users || [];
  }

  // Submit a user to be saved in the database
  public submitUser(user: User): Observable<any> {
    console.log("submitUser", user);
    console.log(this.globals_service.site.restApiUrl + "/users/" + user._id);

    let header = new HttpHeaders();
    header.append("Content-Type", "application/json");

    return (
      this.authHttp
        .put(
          this.globals_service.site.restApiUrl + "/users/" + user._id,
          JSON.stringify({ user: user })
          // { headers: header }
        )
        // .map(res => res.json())
        .catch(error => this.handleError(error))
    );
  }

  // Delete a user from the database
  public deleteUser(_id: string): Observable<any> {
    console.log("deleteUser", _id);

    return this.authHttp.delete(
      this.globals_service.site.restApiUrl + "/users/" + _id
    );
    // .map(res => res.json());
  }

  public getGroups(): Observable<Group[]> {
    return this.authHttp
      .get(this.globals_service.site.restApiUrl + "/groups")
      .map(this.extractGroups)
      .catch(error => this.handleError(error));
  }

  // Generic error handler for connection problems
  private handleError(error) {
    // return Observable.of({
    //   message: error.toString(),
    //   success: false,
    // });

    // console.log(error);

    return Observable.create(observer => {
      observer.next({
        message: error.message,
        success: false
      });
    });
  }
}
