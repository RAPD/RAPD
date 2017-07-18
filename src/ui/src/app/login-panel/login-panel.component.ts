import { Component, OnInit } from '@angular/core';
import { FormGroup,
         FormControl } from '@angular/forms';
import { Router } from '@angular/router';

import { User } from '../shared/interfaces/user';

import { AuthService } from '../shared/services/auth.service';
import { ResultsService } from '../shared/services/results.service';

@Component({
  selector: 'app-login-panel',
  templateUrl: './login-panel.component.html',
  styleUrls: ['./login-panel.component.css'],
  // providers: [ AuthService ]
})
export class LoginPanelComponent implements OnInit {

  login_form: FormGroup;
  submitted: boolean;
  public error_message = '';

  constructor(private auth_service: AuthService,
              private results_service: ResultsService,
              private router: Router) { }

  ngOnInit() {
    this.login_form = new FormGroup({
       email: new FormControl(),
       password: new FormControl()
    });
  }

  onSubmit() {

    this.submitted = true;

    this.auth_service.login(this.login_form.value).subscribe(params => {
      // console.log('onSubmit >>', params);
      if (params.success === true) {
        // Initialize the websocket connection
        this.results_service.initializeWebsocket();
        // Navigate to the dashboard
        this.router.navigate(['dashboard']);
      } else {
        this.error_message = params.message;
      }
      this.submitted = false;
    });
  }
}
