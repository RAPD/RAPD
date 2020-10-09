import { Injectable } from "@angular/core";
// import { Headers,
//          Http } from '@angular/http';
import { CanActivate, Router } from "@angular/router";

import { HttpClient } from "@angular/common/http";
import { JwtHelperService } from "@auth0/angular-jwt";
import { Observable } from "rxjs/Observable";

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

  public login(credentials): Observable<any> {
    // let httpParams = new HttpParams()
    //                        .set('uid', credentials.uid)
    //                        .set('email', credentials.email)
    //                        .set('password', credentials.password);

    // const headers = new HttpHeaders()
    //         .set('Content-Type', 'application/application/json');

    return this.authHttp
      .post(this.globalsService.site.restApiUrl + "authenticate", {
        email: credentials.email,
        password: credentials.password,
        uid: credentials.uid
      })
      .map((res) => this.handleAuth(res))
      .catch((error) => this.handleError(error));
  }

  public requestPass(credentials): Observable<any> {
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

  public changePass(credentials): Observable<any> {
    const profile = JSON.parse(localStorage.getItem("profile"));

    // let creds = 'password=' + credentials.password1 + '&email=' + profile.email;

    // let header = new HttpHeaders();
    // header.append('Content-Type', 'application/x-www-form-urlencoded'); // 'application/json');

    // const headers = new HttpHeaders()
    // .set('Content-Type', 'application/x-www-form-urlencoded');

    // let httpParams = new HttpParams()
    //   .set("email", profile.email)
    //   .set("password", credentials.password);

    return this.authHttp
      .post(this.globalsService.site.restApiUrl + "changepass", {
        email: profile.email,
        password: credentials.password1
      })
      .map((res) => this.handleChangePassReq(res))
      .catch((error) => this.handleError(error));
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

  private handleAuth(res) {
    console.log("handleAuth");
    console.log(res);

    if (res.success === true) {
      // Decode token
      let token = res.token;

      // Save raw token
      localStorage.setItem("access_token", token);
      localStorage.setItem("access_token", token);

      console.log(
        this.helper.decodeToken(token),
        this.helper.getTokenExpirationDate(token),
        this.helper.isTokenExpired(token)
      );

      // Save user information
      let decoded_token = this.helper.decodeToken(token);
      if (decoded_token._doc) {
        var profile = decoded_token._doc;
      } else {
        var profile = decoded_token;
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

  private handlePassReq(res) {
    if (res.success === true) {
      // Return for consumer
      return res;
    } else {
      // Return for consumer
      return res;
    }
  }

  private handleChangePassReq(res) {
    // Convert to JSON
    let res_json = res.json();
    console.log(res_json);

    if (res_json.success === true) {
      // Return for consumer
      return res_json;
    } else {
      // Return for consumer
      return res_json;
    }
  }

  private handleError(error) {
    console.error("An error occurred", error);
    return Observable.of({
      success: false,
      message: error.toString()
    });
  }
}
