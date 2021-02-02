import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { Router } from '@angular/router';

import { Highlight } from '../shared/directives/highlight.directive';
import { RestService } from '../shared/services/rest.service';
import { GlobalsService } from '../shared/services/globals.service';
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
  filteredSessions: Session[] = [];
  errorMessage: string;

  constructor(private globalsService: GlobalsService,
              private restService: RestService,
              private router: Router) { }

  ngOnInit() {
    this.getSessions();
  }

  getSessions() {
    this.restService.getSessions()
      .subscribe(
       sessions => {
         this.filteredSessions = [...sessions];
         this.sessions = sessions;
       },
       error => this.errorMessage = (error as any));
  }

  // Handle a click on the session
  selectSession(event) {

    const id = event.selected[0]._id;

    // Share through globalsService
    this.globalsService.currentSession = id;

    this.router.navigate(['/mx', id]);
  }

  // The filter is changed
  updateSessionFilter(event) {
    const val = event.target.value.toLowerCase();
    // console.log(val);
    // console.log(this.filteredSessions);
    // filter our data
    const temp = this.filteredSessions.filter((d) => {
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
