import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';

import { AuthService } from './shared/services/auth.service';
import { ResultsService } from './shared/services/results.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
})
export class AppComponent {
  title = 'RAPD2';
  mode = 'sessions';

  constructor(private router: Router,
              private auth_service: AuthService,
              private results_service: ResultsService) {}

  ngOnInit() {
    if (this.auth_service.authenticated()) {
      this.results_service.initializeWebsocket();
    }
  }

  changeMode(event) {
    console.log(event.value);
    this.router.navigate(['/' + event.value], { queryParams: {} });
  }
}
