import { Component,
         OnInit,
         ViewContainerRef } from '@angular/core';
import { MdDialogRef,
         MdDialog,
         MdDialogConfig } from '@angular/material';

import { ChangepassDialogComponent } from '../shared/dialogs/changepass-dialog/changepass-dialog.component';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent implements OnInit {

  // changepassDialogRef: MdDialogRef<ChangepassDialogComponent>

  constructor(/*public dialog: MdDialog,
              public viewContainerRef: ViewContainerRef*/) { }

  ngOnInit() {
  }

  // changePass() {
  //   let config = new MdDialogConfig();
  //   config.viewContainerRef = this.viewContainerRef;
  //   this.changepassDialogRef = this.dialog.open(ChangepassDialogComponent, config);
  // }

}
