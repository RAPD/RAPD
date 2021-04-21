import { Injectable, OnInit } from '@angular/core';

@Injectable()
export class Site implements OnInit {

  //
  // Server info
  //
  public restApiUrl: string = 'http://localhost:3000/api/';
  public websocketUrl: string = 'ws://localhost:3000';

  //
  // Authentication info
  //
  // The type of user id expected - email or username
  public auth_user_type: string = 'email';
  public have_users:boolean = true;

  //
  // UI
  //
  // The name of the site - used in the UI
  public name:string = 'NECAT';
  public site_tags:string[] = ['NECAT-C', 'NECAT-E']

  // Label appears in login panel to help guide where user login originates
  public loginLabel = "NE-CAT Remote Login";

  ngOnInit() {}
}
