import { Injectable } from '@angular/core';
// import { Headers,
//          Http } from '@angular/http';
import { CanActivate,
         Router } from '@angular/router';

import { Observable } from 'rxjs/Observable';
// import { AuthHttp } from 'angular2-jwt';
import { HttpClient,
         HttpHeaders,
         HttpParams } from '@angular/common/http';
import { JwtHelperService } from '@auth0/angular-jwt';

import { GlobalsService } from './globals.service';

@Injectable()
export class AuthService implements CanActivate {

  helper = new JwtHelperService();

  constructor(private globals_service: GlobalsService,
              // public http: Http,
              private auth_http: HttpClient,
              private router: Router) { }

  canActivate() {
    return this.authenticated();
  }

  public login(credentials): Observable<any> {

    let httpParams = new HttpParams()
                        .set('uid', credentials.uid)
                        .set('email', credentials.email)
                        .set('password', credentials.password);

    return this.auth_http.post(
      this.globals_service.site.restApiUrl + 'authenticate',
      httpParams
    )
    .map(res => this.handleAuth(res))
    .catch(error => this.handleError(error));
  }

  public requestPass(credentials): Observable<any> {

    console.log('requestPass', credentials);

    let creds = 'email=' + credentials.email;
    // console.log(creds);

    let header = new HttpHeaders();
    header.append('Content-Type', 'application/x-www-form-urlencoded'); // 'application/json');
    console.log(header);

    return this.auth_http.post(
      this.globals_service.site.restApiUrl + 'requestpass',
      creds,
      // {headers: header}
    )
    // .map(res => res.json())
    .map(res => this.handlePassReq(res))
    .catch(error => this.handleError(error));
  }

  public changePass(credentials): Observable<any> {

    let profile = JSON.parse(localStorage.getItem('profile'));

    let creds = 'password=' + credentials.password1 + '&email=' + profile.email;

    let header = new HttpHeaders();
    header.append('Content-Type', 'application/x-www-form-urlencoded'); // 'application/json');

    return this.auth_http.post(
      this.globals_service.site.restApiUrl + 'changepass',
      creds,
      // {headers: header}
    )
    // .map(res => res.json())
    .map(res => this.handleChangePassReq(res))
    .catch(error => this.handleError(error));
  }

  handleAuth(res) {

    console.log('handleAuth');
    console.log(res);

    if (res.success === true) {
      // Decode token
      let token = res.token;

      // Save raw token
      localStorage.setItem('access_token', token);
      localStorage.setItem('access_token', token);
      

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
      localStorage.setItem('profile', JSON.stringify(profile));

      // Return for consumer
      return res;
    } else {
      // Return for consumer
      return res;
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
      // localStorage.setItem('access_token', token);

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
      // localStorage.setItem('access_token', token);

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
    // This searches for an item in localStorage with key == 'access_token'
    let token = localStorage.getItem('access_token');
    // console.log(token);

    if (token === null) {
      return false;
    } else {
      // console.log(
      //   this.jwtHelper.decodeToken(token),
      //   this.jwtHelper.getTokenExpirationDate(token),
      //   ! this.jwtHelper.isTokenExpired(token)
      // );
      return ! this.helper.isTokenExpired(token);
    }
  }

  public logout() {

    // console.log('logout');

    // Remove token from localStorage
    localStorage.removeItem('access_token');
    localStorage.removeItem('profile');

    // this.userProfile = undefined;
    // Redirect to home
    // window.location.href = 'http://localhost:4200';
    //window.location.href = 'http://'+window.location.host;
    this.router.navigate(['/']);

  }
}
