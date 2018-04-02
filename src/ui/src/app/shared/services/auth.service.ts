import { Injectable } from '@angular/core';
import { Headers,
         Http } from '@angular/http';
import { CanActivate,
         Router } from '@angular/router';

import { Observable } from 'rxjs/Observable';
import { AuthHttp,
         JwtHelper } from 'angular2-jwt';

import { GlobalsService } from './globals.service';

@Injectable()
export class AuthService implements CanActivate {

  jwtHelper: JwtHelper = new JwtHelper();

  constructor(private globals_service: GlobalsService,
              public http: Http,
              private auth_http: AuthHttp,
              private router: Router) { }

  canActivate() {
    return this.authenticated();
  }

  public login(credentials): Observable<any> {

    // console.log('this.globals_service.site.restApiUrl', this.globals_service.site.restApiUrl);

    // console.log('login', credentials);

    let creds = 'uid=' + credentials.uid + '&email=' + credentials.email+ '&password=' + credentials.password;
    // console.log(creds);

    let header = new Headers();
    header.append('Content-Type', 'application/x-www-form-urlencoded'); // 'application/json');

    return this.http.post(
      this.globals_service.site.restApiUrl + 'authenticate',
      creds,
      {headers: header}
    )
    // .map(res => res.json())
    .map(res => this.handleAuth(res))
    .catch(error => this.handleError(error));
  }

  public requestPass(credentials): Observable<any> {

    console.log('requestPass', credentials);

    let creds = 'email=' + credentials.email;
    // console.log(creds);

    let header = new Headers();
    header.append('Content-Type', 'application/x-www-form-urlencoded'); // 'application/json');
    console.log(header);

    return this.http.post(
      this.globals_service.site.restApiUrl + 'requestpass',
      creds,
      {headers: header}
    )
    // .map(res => res.json())
    .map(res => this.handlePassReq(res))
    .catch(error => this.handleError(error));
  }

  public changePass(credentials): Observable<any> {

    let profile = JSON.parse(localStorage.getItem('profile'));

    let creds = 'password=' + credentials.password1 + '&email=' + profile.email;

    let header = new Headers();
    header.append('Content-Type', 'application/x-www-form-urlencoded'); // 'application/json');

    return this.auth_http.post(
      this.globals_service.site.restApiUrl + 'changepass',
      creds,
      {headers: header}
    )
    // .map(res => res.json())
    .map(res => this.handleChangePassReq(res))
    .catch(error => this.handleError(error));
  }

  handleAuth(res) {

    // Convert to JSON
    let res_json = res.json();
    console.log(res_json);

    if (res_json.success === true) {
      // Decode token
      let token = res_json.token;

      // Save raw token
      localStorage.setItem('id_token', token);

      console.log(
        this.jwtHelper.decodeToken(token),
        this.jwtHelper.getTokenExpirationDate(token),
        this.jwtHelper.isTokenExpired(token)
      );

      // Save user information
      let decoded_token = this.jwtHelper.decodeToken(token);
      if (decoded_token._doc) {
        var profile = decoded_token._doc;
      } else {
        var profile = decoded_token;
      }
      console.log(profile);
      localStorage.setItem('profile', JSON.stringify(profile));

      // Return for consumer
      return res_json;
    } else {
      // Return for consumer
      return res_json;
    }
  }

  handlePassReq(res) {

    // Convert to JSON
    let res_json = res.json();
    // console.log(res_json);

    if (res_json.success === true) {
      // Decode token
      // let token = res_json.token;

      // Save raw token
      // localStorage.setItem('id_token', token);

      // console.log(
      //   this.jwtHelper.decodeToken(token),
      //   this.jwtHelper.getTokenExpirationDate(token),
      //   this.jwtHelper.isTokenExpired(token)
      // );

      // Save user information
      // let profile = this.jwtHelper.decodeToken(token)._doc;
      // localStorage.setItem('profile', JSON.stringify(profile));

      // Return for consumer
      return res_json;
    } else {
      // Return for consumer
      return res_json;
    }
  }

  handleChangePassReq(res) {

    // Convert to JSON
    let res_json = res.json();
    console.log(res_json);

    if (res_json.success === true) {
      // Decode token
      // let token = res_json.token;

      // Save raw token
      // localStorage.setItem('id_token', token);

      // console.log(
      //   this.jwtHelper.decodeToken(token),
      //   this.jwtHelper.getTokenExpirationDate(token),
      //   this.jwtHelper.isTokenExpired(token)
      // );

      // Save user information
      // let profile = this.jwtHelper.decodeToken(token)._doc;
      // localStorage.setItem('profile', JSON.stringify(profile));

      // Return for consumer
      return res_json;
    } else {
      // Return for consumer
      return res_json;
    }
  }

  private handleError(error) {
    console.error('An error occurred', error);
    return Observable.of({
      success: false,
      message: error.toString()
    });
  }

  public authenticated() {

    // console.log('authenticated');

    // Check if there's an unexpired JWT
    // This searches for an item in localStorage with key == 'id_token'
    let token = localStorage.getItem('id_token');
    // console.log(token);

    if (token === null) {
      return false;
    } else {
      // console.log(
      //   this.jwtHelper.decodeToken(token),
      //   this.jwtHelper.getTokenExpirationDate(token),
      //   ! this.jwtHelper.isTokenExpired(token)
      // );
      return ! this.jwtHelper.isTokenExpired(token);
    }
  }

  public logout() {

    // console.log('logout');

    // Remove token from localStorage
    localStorage.removeItem('id_token');
    localStorage.removeItem('profile');

    // this.userProfile = undefined;
    // Redirect to home
    // window.location.href = 'http://localhost:4200';
    //window.location.href = 'http://'+window.location.host;
    this.router.navigate(['/']);

  }
}
