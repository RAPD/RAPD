import { Component,
         EventEmitter,
         OnInit,
         Output,
         ViewContainerRef } from '@angular/core';
import { MatDialog,
         MatDialogRef,
         MatDialogConfig } from '@angular/material';

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

  constructor(private auth_service: AuthService,
              private globals_service: GlobalsService,
              public dialog: MatDialog,
              public viewContainerRef: ViewContainerRef) {}

  ngOnInit() {
  }

  changeMode(mode: string) {
    this.modeChange.emit({
      value: mode
    });
  }

  openLoginDialog() {

    let config = new MatDialogConfig();
    config.viewContainerRef = this.viewContainerRef;

    this.loginDialogRef = this.dialog.open(LoginDialogComponent, config);

    this.loginDialogRef.afterClosed().subscribe(result => {
      // console.log('closed', result);
      this.loginDialogRef = null;
      if (result) {
        if (result.pass_force_change == true) {
          let config = new MatDialogConfig();
          config.viewContainerRef = this.viewContainerRef;
          this.changepassDialogRef = this.dialog.open(ChangepassDialogComponent, config);
        }
      }
    });
  }
}
