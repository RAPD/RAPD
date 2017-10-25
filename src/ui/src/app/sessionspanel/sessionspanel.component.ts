import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { Router } from '@angular/router';

import { Highlight } from '../shared/directives/highlight.directive';
import { RestService } from '../shared/services/rest.service';
import { Session } from '../shared/classes/session';

@Component({
  selector: 'app-sessionspanel',
  templateUrl: './sessionspanel.component.html',
  styleUrls: ['./sessionspanel.component.css'],
  // directives: [ Highlight ],
  // providers: [ SessionService ]
})
export class SessionspanelComponent implements OnInit {

  sessions: Session[];
  errorMessage: string;

  constructor(private rest_service: RestService,
              private router: Router) { }

  ngOnInit() {
    this.getSessions();
  }

  getSessions() {
    this.rest_service.getSessions()
      .subscribe(
       sessions => this.sessions = sessions,
       error => this.errorMessage = <any>error);
  }

  // Handle a click on the session
  selectSession(event) {

    let id = event.selected[0]._id

    this.router.navigate(['/mx', id]);
  }

}
