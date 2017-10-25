import { Injectable, OnInit } from '@angular/core';

@Injectable()
export class Site implements OnInit {

  //
  // Server info
  //
  public restApiUrl: string = 'http://localhost:3000/api/';
  // public apiUrl: string = 'http://my_production_server:3000/api/';
  public websocketUrl: string = 'ws://localhost:3000';

  //
  // Authentication info
  //
  // The type of user id expected - email or username
  public authUserType: string = 'email';
  public have_users:boolean = false;

  //
  // UI
  //

  // The name of the site - used in the UI
  public name:string = 'SERCAT';
  public site_tags:string[] = ['NECAT-C', 'NECAT-E']

  ngOnInit() {
  }
}
