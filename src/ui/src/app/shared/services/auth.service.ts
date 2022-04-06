import { Injectable } from "@angular/core";
import { CanActivate, Router } from "@angular/router";

import { HttpClient, HttpErrorResponse } from "@angular/common/http";
import { JwtHelperService } from "@auth0/angular-jwt";
import { Observable } from "rxjs/Observable";
import { of } from 'rxjs';
import { map, catchError } from 'rxjs/operators';

import { GlobalsService } from "./globals.service";

@Injectable()
export class AuthService implements CanActivate {

  private helper = new JwtHelperService();

  constructor(
    private globalsService: GlobalsService,
    private authHttp: HttpClient,
    private router: Router
  ) {}

  public canActivate() {
    return this.authenticated();
  }

  public login(credentials: any): Observable<any> {

    const self = this;

    return this.authHttp
      .post<any>(this.globalsService.site.restApiUrl + "authenticate", {
        email: credentials.email,
        password: credentials.password,
        uid: credentials.uid,
      })
      .pipe(
        map(res => self.handleAuth(res)),
        catchError((err) => of({success: false, message: err}))
      );
  }

  public requestPass(credentials: any): Observable<any> {
    console.log("requestPass", credentials);

    // let httpParams = new HttpParams()
    //                        .set('email', credentials.email);

    // const headers = new HttpHeaders()
    //   .set('Content-Type', 'application/application/json');

    return this.authHttp
      .post(this.globalsService.site.restApiUrl + "requestpass", {
        email: credentials.email
      })
      .map((res) => this.handlePassReq(res))
      .catch((error) => this.handleError(error));
  }

  public changePass(credentials: any): Observable<any> {

    const profile = JSON.parse(localStorage.getItem('profile'));
    const self = this;

    return this.authHttp
      .post(this.globalsService.site.restApiUrl + "changepass", {
        email: profile.email,
        password: credentials.password1,
      })
      .pipe(
        map(res => self.handleChangePassReq(res)),
        catchError((err) => of({success: false, message: err}))
      );
      // .map((res) => this.handleChangePassReq(res))
      // .catch((error) => this.handleError(error));
  }

  public authenticated() {
    // console.log('authenticated');

    // Check if there's an unexpired JWT
    // This searches for an item in localStorage with key == 'access_token'
    let token = localStorage.getItem("access_token");
    // console.log(token);

    if (token === null) {
      return false;
    } else {
      // console.log(
      //   this.jwtHelper.decodeToken(token),
      //   this.jwtHelper.getTokenExpirationDate(token),
      //   ! this.jwtHelper.isTokenExpired(token)
      // );
      return !this.helper.isTokenExpired(token);
    }
  }

  public logout() {
    // console.log('logout');

    // Remove token from localStorage
    localStorage.removeItem("access_token");
    localStorage.removeItem("profile");

    // this.userProfile = undefined;
    // Redirect to home
    // window.location.href = 'http://localhost:4200';
    //window.location.href = 'http://'+window.location.host;
    this.router.navigate(["/"]);
  }

  private handleAuth(res: any) {
    console.log("handleAuth");
    console.log(res);

    if (res.success === true) {
      // Decode token
      const token = res.token;

      // Save raw token
      localStorage.setItem("access_token", token);
      localStorage.setItem("access_token", token);

      console.log(
        this.helper.decodeToken(token),
        this.helper.getTokenExpirationDate(token),
        this.helper.isTokenExpired(token)
      );

      // Save user information
      const decodedToken = this.helper.decodeToken(token);
      let profile;
      if (decodedToken._doc) {
        profile = decodedToken._doc;
      } else {
        profile = decodedToken;
      }
      console.log(profile);
      localStorage.setItem("profile", JSON.stringify(profile));

      // Return for consumer
      return res;
    } else {
      // Return for consumer
      return res;
    }
  }

  private handlePassReq(res: any) {
    if (res.success === true) {
      // Return for consumer
      return res;
    } else {
      // Return for consumer
      return res;
    }
  }

  private handleChangePassReq(res: any) {
    // Convert to JSON
    const resJson = res.json();
    // console.log(resJson);

    if (resJson.success === true) {
      // Return for consumer
      return resJson;
    } else {
      // Return for consumer
      return resJson;
    }
  }

  private handleError(error: HttpErrorResponse): Observable<any>  {
    console.error("An error occurred", error);
    return Observable.of({
      success: false,
      message: error,
    });
  }
}
