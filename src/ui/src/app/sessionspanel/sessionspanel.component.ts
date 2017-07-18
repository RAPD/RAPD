import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { Router } from '@angular/router';

import { Highlight } from '../shared/directives/highlight.directive';
import { SessionService } from '../shared/services/session.service';
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

  constructor(private session_service: SessionService,
              private router: Router) { }

  ngOnInit() {
    this.getSessions();
  }

  getSessions() {
    this.session_service.getSessions()
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
