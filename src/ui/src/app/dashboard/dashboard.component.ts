import { Component,
         OnInit,
         ViewContainerRef } from '@angular/core';
import { MdDialogRef,
         MdDialog,
         MdDialogConfig } from '@angular/material';

import { User } from '../shared/classes/user';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent implements OnInit {

  // changepassDialogRef: MdDialogRef<ChangepassDialogComponent>
  user: User;
  master_on: boolean = true;

  constructor(/*public dialog: MdDialog,
              public viewContainerRef: ViewContainerRef*/) { }

  ngOnInit() {

    // Get the user profile
    this.user = JSON.parse(localStorage.getItem('profile'));

  }



}
