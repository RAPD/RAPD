import { Component,
         OnInit,
         ViewContainerRef } from '@angular/core';
import { FormGroup,
         FormControl } from '@angular/forms';
import { MatDialogRef } from '@angular/material/dialog';
import { Router } from '@angular/router';

import { AuthService } from '../../shared/services/auth.service';
import { WebsocketService } from '../../shared/services/websocket.service';
import { GlobalsService } from '../../shared/services/globals.service';

@Component({
  selector: 'app-login-dialog',
  templateUrl: './login-dialog.component.html',
  styleUrls: ['./login-dialog.component.css']
})
export class LoginDialogComponent implements OnInit {

  mode: string;
  login_form: FormGroup;
  lostpass_form: FormGroup;
  submitted: boolean;
  show_request_success: boolean;
  returnedParams: any;
  public submit_error = '';

  constructor(private auth_service: AuthService,
              private websocket_service: WebsocketService,
              private router: Router,
              public globalsService: GlobalsService,
              public dialogRef: MatDialogRef<LoginDialogComponent>) { }

  ngOnInit() {

    this.mode = 'login';

    this.login_form = new FormGroup({
       email: new FormControl(),
       uid: new FormControl(),
       password: new FormControl(),
    });

    this.lostpass_form= new FormGroup({
      email: new FormControl(),
    });
  }

  onSubmitLogin() {

    const self = this;

    this.submitted = true;

    // console.log('this.login_form.value:', this.login_form.value);

    this.auth_service.login(this.login_form.value).subscribe(params => {
      // console.log('onSubmit >>', params);
      self.returnedParams = params;
      if (params.success === true) {
        // Initialize the websocket connection
        this.websocket_service.initializeWebsocket();
        // Navigate to the dashboard
        this.router.navigate(['dashboard']);
        this.mode = 'show_login_success';
        // Close dialog
        setTimeout(() => {
          self.dialogRef.close(params)
        }, 5000);
      } else {
        console.log('Error', params);
        self.submit_error = params.message;
      }
      this.submitted = false;
    });
  }

  onSubmitLostpass() {

    const self = this;

    this.submitted = true;

    this.auth_service.requestPass(this.lostpass_form.value).subscribe(params => {
      self.returnedParams = params;
      self.submitted = false;

      if (params.success === true) {
        self.mode = 'show_request_success';
        setTimeout(() => {self.dialogRef.close(params)}, 5000);
      } else {
        self.submit_error = params.message;
      }
    });
  }

  exitLogin() {
    console.log("exitLogin");
    this.dialogRef.close(this.returnedParams);
  }

}
