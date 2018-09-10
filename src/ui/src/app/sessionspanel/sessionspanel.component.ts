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

  sessions: Session[] = [];
  filtered_sessions: Session[] = [];
  errorMessage: string;

  constructor(private rest_service: RestService,
              private router: Router) { }

  ngOnInit() {
    this.getSessions();
  }

  getSessions() {
    this.rest_service.getSessions()
      .subscribe(
       sessions => {
         this.filtered_sessions = [...sessions];
         this.sessions = sessions;
       },
       error => this.errorMessage = <any>error);
  }

  // Handle a click on the session
  selectSession(event) {

    let id = event.selected[0]._id

    this.router.navigate(['/mx', id]);
  }

  // The filter is changed
  updateSessionFilter(event) {
    const val = event.target.value.toLowerCase();
    // console.log(val);
    // console.log(this.filtered_sessions);
    // filter our data
    const temp = this.filtered_sessions.filter(function(d) {
      // console.log(d);
      try {
        return d.group.groupname.toLowerCase().indexOf(val) !== -1 ||
             d.site.toLowerCase().indexOf(val) !== -1 ||
             d.data_root_directory.toLowerCase().indexOf(val) !== -1 ||
            //  d.last_process.indexOf(val) !== -1 ||
             !val;
      } catch (error) {
        return false;
      }
    });

    // update the rows
    this.sessions = temp;
  }

}
