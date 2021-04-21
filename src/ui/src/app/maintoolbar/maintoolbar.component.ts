import { Component,
         EventEmitter,
         OnInit,
         Output,
         ViewContainerRef } from '@angular/core';
import { MatDialog, MatDialogRef, MatDialogConfig } from '@angular/material/dialog';

import { LoginDialogComponent } from './login-dialog/login-dialog.component';
import { ChangepassDialogComponent } from '../shared/dialogs/changepass-dialog/changepass-dialog.component';
import { AuthService } from '../shared/services/auth.service';
import { GlobalsService } from '../shared/services/globals.service';

@Component({
  selector: 'app-maintoolbar',
  templateUrl: './maintoolbar.component.html',
  styleUrls: ['./maintoolbar.component.css'],
})
export class MaintoolbarComponent implements OnInit {

  @Output() modeChange = new EventEmitter();

  loginDialogRef: MatDialogRef<LoginDialogComponent>;
  changepassDialogRef: MatDialogRef<ChangepassDialogComponent>;

  constructor(public auth_service: AuthService,
              public globals_service: GlobalsService,
              public dialog: MatDialog,
              public viewContainerRef: ViewContainerRef) {}

  ngOnInit() {}

  changeMode(mode: string) {
    this.modeChange.emit({
      value: mode,
    });
  }

  openLoginDialog() {

    const dialogConfig = new MatDialogConfig();
    dialogConfig.viewContainerRef = this.viewContainerRef;
    dialogConfig.disableClose = true;
    dialogConfig.autoFocus = true;

    this.loginDialogRef = this.dialog.open(LoginDialogComponent, dialogConfig);

    this.loginDialogRef.afterClosed().subscribe(result => {
      console.log(result);
      this.loginDialogRef = null;
      if (result) {
        if (result.pass_force_change === true) {
          console.log("Pop open the change password dialog");
          const changeDialogConfig = new MatDialogConfig();
          changeDialogConfig.viewContainerRef = this.viewContainerRef;
          changeDialogConfig.disableClose = true;
          changeDialogConfig.autoFocus = true;
          this.changepassDialogRef = this.dialog.open(ChangepassDialogComponent, changeDialogConfig);
        }
      }
    });
  }
}
