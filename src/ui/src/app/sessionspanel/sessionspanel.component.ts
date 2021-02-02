import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { Router } from '@angular/router';

import { PageEvent } from '@angular/material/paginator';
import { Sort } from '@angular/material/sort';

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

  // Data source for material design table
  public dataSource = [];
  // Data settings for material design table
  public dataSettings: any = {
    pageIndex: 0,
    pageSize: 20,
    query: {},
    searchKey: undefined,
    searchOrder: "asc",
  };
  // Default displayed columns
  public displayedColumns: string[] = [
    // "_id",
    "site",
    "group_name",
    "timestamp",
    "last_process",
    "data_root_dir",
  ];
  // Order for column display
  public columnOrder = [
    "_id",
    "site",
    "group_name",
    "timestamp",
    "last_process",
    "data_root_dir",
  ];
  // Clone to use
  public allColumns = Object.assign([], this.columnOrder);
  // Columns that do not need to be modified to display
  public asIsColumns = [
    "_id",
    "data_root_dir",
    "site",
  ]
  // Labels to use
  public columnLabels:any = {
    "_id":"_id",
    "group_name":"Group",
    "timestamp":"Created",
    "data_root_dir":"Directory",
    "last_process":"Last Process",
    "site":"Beamline",
  };

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
         console.log(sessions[3]);
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

  //
  // Methods for MaterialDesign table
  //
  public handlePaginator(page:PageEvent) {}

  public handleSort(sort:Sort) {}

  public recordClick(record:any, event:any) {}

}
