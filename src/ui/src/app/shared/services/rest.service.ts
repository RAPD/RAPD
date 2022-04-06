import { HttpClient, HttpHeaders } from "@angular/common/http";
import { Injectable } from "@angular/core";
// import { Headers, Response } from "@angular/http";
import { Observable } from "rxjs/Observable";
import { Subscriber } from "rxjs/Subscriber";
import { of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
// import * as moment from "moment-mini";

import { GlobalsService } from "./globals.service";

import { Group } from "../classes/group";
import { Image } from "../classes/image";
import { Project } from "../classes/project";
import { Run } from "../classes/run";
import { Session } from "../classes/session";
import { User } from "../classes/user";
import { isDataSource } from "@angular/cdk/collections";

function baseName(str: string): string {
  let base = new String(str).substring(str.lastIndexOf("/") + 1);
  if (base.lastIndexOf(".") !== -1)
    base = base.substring(0, base.lastIndexOf("."));
  return base;
}

@Injectable()
export class RestService {
  constructor(
    private globalsService: GlobalsService,
    private authHttp: HttpClient
  ) {}

  //
  // DASHBOARD METHODS
  //
  public getDashboardResults(): Observable<any> {
    // console.log('getDashboardResults');

    return (
      this.authHttp
        .get(this.globalsService.site.restApiUrl + "/dashboard/results")
        .pipe(catchError((err) => of({success: false, message: err})))
    );
  }

  public getDashboardLogins(): Observable<any> {
    // console.log('getDashboardLogins');

    return (
      this.authHttp
        .get(this.globalsService.site.restApiUrl + "/dashboard/logins")
        .pipe(catchError((err) => of({success: false, message: err})))
    );
  }

  public getServerActivities(): Observable<any> {
    // console.log('getServerActivities');

    return (
      this.authHttp
        .get(this.globalsService.site.restApiUrl + '/dashboard/server_activities')
        .pipe(catchError((err) => of({success: false, message: err})))
    );
  }

  //
  // DOWNLOAD METHODS
  //

  // Request a download
  public getDownloadById(id: string, filename: string): void {
    console.log("getDownloadById", id, filename);

    this.authHttp
      .get(this.globalsService.site.restApiUrl + "/download_by_id/" + id, {
        responseType: "text",
      })
      .subscribe(res => {
        // Convert base64 string to byte array
        const byteCharacters = atob(<any>res);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        // Convert byte array to Blob
        const blob = new Blob([byteArray], {
          type: "application/octet-stream",
        });
        // Create ObjectURL
        const url = window.URL.createObjectURL(blob);
        // Create DOM element with download attribute
        const pom = document.createElement("a");
        pom.setAttribute("href", url);
        pom.setAttribute("download", filename);
        // Now trigger download
        if (document.createEvent) {
          const event = document.createEvent("MouseEvents");
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
      .get(this.globalsService.site.restApiUrl + "/download_by_hash/" + hash, {
        responseType: "text",
      })
      .subscribe(res => {
        // Convert base64 string to byte array
        const byteCharacters = atob(res);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        // Convert byte array to Blob
        const blob = new Blob([byteArray], {
          type: "application/octet-stream",
        });
        // Create ObjectURL
        const url = window.URL.createObjectURL(blob);
        // Create DOM element with download attribute
        const pom = document.createElement("a");
        pom.setAttribute("href", url);
        pom.setAttribute("download", filename);
        // Now trigger download
        if (document.createEvent) {
          const event = document.createEvent("MouseEvents");
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
      .get(this.globalsService.site.restApiUrl + "/get_pdb_by_hash/" + hash, {
        responseType: "text",
      }).subscribe(res => {
        console.log(res);
      });
  }

  public getPdb(pdbFile: string) {
    console.log("getPdb", pdbFile);

    return (this.authHttp
      .get(this.globalsService.site.restApiUrl + "/download_pdb/" + pdbFile, {
        responseType: "text",
      }));
      // .subscribe(res => {
      //   console.log(res);
      // });
  }

  public getMap(mapFile: string) {
    console.log("getMap", mapFile);

    return (this.authHttp
      .get(this.globalsService.site.restApiUrl + "/download_map/" + mapFile, {
        responseType: "arraybuffer",
      }));
      // .subscribe(res => {
      //   console.log(res);
      // });
  }

  //
  // GROUP METHODS
  //
  public extractGroups(res: any, error: any) {
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

    // let header = new HttpHeaders();
    // header.append("Content-Type", "application/json"); // 'application/x-www-form-urlencoded'

    return (
      this.authHttp
        .put(
          this.globalsService.site.restApiUrl + "/groups/" + group._id,
          JSON.stringify({group})
        )
        .pipe(
          map(this.extractGroups),
          catchError((err) => of({success: false, message: err}))
        )
    );
  }

  // Delete a group from the database
  public deleteGroup(_id: string): Observable<any> {
    // console.log("deleteGroup", _id);

    return this.authHttp.delete(
      this.globalsService.site.restApiUrl + "/groups/" + _id
    )
    .pipe(catchError((err) => of({success: false, message: err})))
  }

  // Call to populate groups from LDAP server
  public populateGroups(): Observable<any> {
    return (
      this.authHttp
        .get(this.globalsService.site.restApiUrl + "/groups/populate")
        .pipe(catchError((err) => of({success: false, message: err})))
    );
  }

  //
  // IMAGE METHODS
  //
  public getImageData(_id: string): Observable<Image> {
    // console.log("getImageData _id:", _id);

    return this.authHttp.get(
      this.globalsService.site.restApiUrl + "/images/" + _id
    )
    .pipe(catchError((err) => of({success: false, message: err})))
  }

  public getImageJpeg(request: any): Observable<any> {
    // console.log('getImageJpeg', request);

    const req = JSON.stringify(request);
    // console.log(req);

    return this.authHttp
      .get(this.globalsService.site.restApiUrl + "/image_jpeg/" + req)
      // .map(res => {
      //   console.log(res);
      //   // return res.json();
      // })
      .pipe(catchError((err) => of({success: false, message: err})))
  }
  //
  // JOB methods
  //
  public submitJob(request: any): Observable<any> {

    // console.log('submitJob', request);

    return (
      this.authHttp
        .put(
          this.globalsService.site.restApiUrl + "/jobs/submit",
          JSON.stringify({ request })
        )
        .pipe(catchError((err) => of({success: false, message: err})))
    );
  }

  //
  // OVERWATCH methods
  //
  public getOverwatches(): Observable<any> {
    // console.log('getOverwatches');

    return (
      this.authHttp
        .get(this.globalsService.site.restApiUrl + "/overwatches")
        .pipe(catchError((err) => of({success: false, message: err})))
    );
  }

  public stopOverwatch(id: string) {
    return (
      this.authHttp
        .put(
          this.globalsService.site.restApiUrl + "/overwatches/stop/" + id,
          JSON.stringify({id})
        )
        .pipe(catchError((err) => of({success: false, message: err})))
    );
  }

  public stopAllOverwatches() {
    // console.log('stopAllOverwatches');

    return (
      this.authHttp
        .put(
          this.globalsService.site.restApiUrl + "/overwatches/stopall",
          JSON.stringify({ id: "foo" })
        )
        .pipe(catchError((err) => of({success: false, message: err})))
    );
  }

  public startOverwatch(id: string) {

    return (
      this.authHttp
        .put(
          this.globalsService.site.restApiUrl + "/overwatches/start/" + id,
          JSON.stringify({id})
        )
        .pipe(catchError((err) => of({success: false, message: err})))
    );
  }

  //
  // PDB Methods
  //
  public getUploadedPdbsBySession(id: string): Observable<any> {
    // console.log("getUploadedPdbsBySession", id);

    return this.authHttp
      .get(this.globalsService.site.restApiUrl + "/pdbs/by_session/" + id)
      .pipe(catchError((err) => of({success: false, message: err})))
  }

  //
  // PROJECT methods
  //
  public getProjects(): Observable<any> {
    // console.log("getProjects");

    return this.authHttp
      .get(this.globalsService.site.restApiUrl + "/projects")
      .pipe(catchError((err) => of({success: false, message: err})))
  }

  public getProjectsBySession(id: string): Observable<any> {
    // console.log("getProjectsBySession", id);

    return this.authHttp
      .get(this.globalsService.site.restApiUrl + "/projects/by_session/" + id)
      .pipe(catchError((err) => of({success: false, message: err})))
  }

  public getProject(id: string): Observable<any> {
    // console.log("getProject", id);

    return (
      this.authHttp
        .get(this.globalsService.site.restApiUrl + "/projects/" + id)
        .pipe(catchError((err) => of({success: false, message: err})))
    );
  }

  public submitProject(project: Project): Observable<any> {
    // console.log("submitProject", project);
    // console.log(
    //   this.globalsService.site.restApiUrl + "/projects/" + project._id
    // );

    return (
      this.authHttp
        .put(
          this.globalsService.site.restApiUrl + "/projects/" + project._id,
          JSON.stringify({project})
        )
        .pipe(catchError((err) => of({success: false, message: err})))
    );
  }

  // Delete a project from the database
  public deleteProject(_id: string): Observable<any> {
    // console.log("deleteProject", _id);

    return (
      this.authHttp
        .delete(this.globalsService.site.restApiUrl + "/projects/" + _id)
        .pipe(catchError((err) => of({success: false, message: err})))
    );
  }

  public addResultToProject(data: any): Observable<any> {
    // console.log("addResultToProject");

    return (
      this.authHttp
        .put(
          this.globalsService.site.restApiUrl + "/projects_add_result",
          JSON.stringify({
            project_id: data._id,
            result: data.result,
          })
        )
        .pipe(catchError((err) => of({success: false, message: err})))
    );
  }

  //
  // RESULT METHODS
  //
  public getResult(_id: string): Observable<any> {
    return (
      this.authHttp
        .get(this.globalsService.site.restApiUrl + "/results/" + _id)
        .pipe(catchError((err) => of({success: false, message: err})))
    );
  }

  public getResultDetail(_id: string): Observable<any> {
    // console.log("getResultDetail", _id);

    return (
      this.authHttp
        .get(this.globalsService.site.restApiUrl + "/result_details/" + _id)
        .pipe(catchError((err) => of({success: false, message: err})))
    );
  }

  public getMultipleResultDetails(ids: string[]): Observable<any> {
    // console.log("getMultipleResultDetail", ids);

    return (
      this.authHttp
        .get(this.globalsService.site.restApiUrl + "/result_details/multiple", {
          params: {ids:JSON.stringify(ids)},
        })
        .pipe(catchError((err) => of({success: false, message: err})))
    );
  }

  //
  // RUN methods
  //
  public getRunData(_id: string): Observable<Run> {
    // console.log('getRunData _id:', _id);

    return (
      this.authHttp
        .get(this.globalsService.site.restApiUrl + "/runs/" + _id)
        .pipe(catchError((err) => of({success: false, message: err})))
    );
  }

  //
  // SESSIONS
  //
  public getSessions(): Observable<Session[]> | Observable<any>{
    // console.log("getSessions");
    return this.authHttp
      .get(this.globalsService.site.restApiUrl + "/sessions")
      .map(this.extractSessions)
      .pipe(
        map(this.extractSessions),
        catchError((err) => of({success: false, message: err}))
      )
  }

  private extractSessions(res:any, error:any) {
    // console.error(res);
    // let body = res.json();
    return res.sessions || [];
  }

  // Submit a session to be saved in the database
  public submitSession(session: Session): Observable<any> {
    // console.log("submitSession");

    return (
      this.authHttp
        .put(
          this.globalsService.site.restApiUrl + "/sessions/" + session._id,
          JSON.stringify({session})
        )
        .pipe(catchError((err) => of({success: false, message: err})))
    );
  }

  // Delete a user from the database
  public deleteSession(_id: string): Observable<any> {
    // console.log("deleteSession", _id);

    return this.authHttp.delete(
      this.globalsService.site.restApiUrl + "/sessions/" + _id
    )
    .pipe(catchError((err) => of({success: false, message: err})))
  }

  //
  // USERS
  //
  public getUsers(): Observable<User[]> | Observable<any>{
    // console.log("getUsers");

    return this.authHttp
      .get(this.globalsService.site.restApiUrl + "/users")
      .pipe(
        map(this.extractUsers),
        catchError((err) => of({success: false, message: err}))
      )
  }

  private extractUsers(res: any, error: any) {
    return res.users || [];
  }

  // Submit a user to be saved in the database
  public submitUser(user: User): Observable<any> {
    // console.log("submitUser", user);
    // console.log(this.globalsService.site.restApiUrl + "/users/" + user._id);

    return (
      this.authHttp
        .put(
          this.globalsService.site.restApiUrl + "/users/" + user._id,
          JSON.stringify({user})
        )
        .pipe(catchError((err) => of({success: false, message: err})))
    );
  }

  // Delete a user from the database
  public deleteUser(_id: string): Observable<any> {
    // console.log("deleteUser", _id);

    return this.authHttp.delete(
      this.globalsService.site.restApiUrl + "/users/" + _id
    )
    .pipe(catchError((err) => of({success: false, message: err})))
  }

  public getGroups(): Observable<Group[]> | Observable<any>{
    return this.authHttp
      .get(this.globalsService.site.restApiUrl + "/groups")
      .pipe(
        map(this.extractGroups),
        catchError((err) => of({success: false, message: err}))
      )
  }
}
