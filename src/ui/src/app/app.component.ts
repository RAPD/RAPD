import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';

import { AuthService } from './shared/services/auth.service';
import { WebsocketService } from './shared/services/websocket.service';

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
              private websocket_service: WebsocketService) {}

  ngOnInit() {
    if (this.auth_service.authenticated()) {
      this.websocket_service.initializeWebsocket();
    }
  }

  changeMode(event) {
    // console.log(event.value);
    this.router.navigate(['/' + event.value], { queryParams: {} });
  }
}
