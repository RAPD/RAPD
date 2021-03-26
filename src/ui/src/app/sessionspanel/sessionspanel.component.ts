// import { DataSource } from '@angular/cdk/collections';
import { AfterViewInit,
         ChangeDetectorRef,
         Component,
         OnInit,
        //  Output,
        //  EventEmitter,
         ViewChild } from '@angular/core';
import { Router } from '@angular/router';
import { MatPaginator } from '@angular/material/paginator';
// import { MatSnackBar } from '@angular/material/snack-bar';
import { MatSort, MatSortable } from '@angular/material/sort';
// import { Sort } from '@angular/material/sort';

import { tap } from 'rxjs/operators';

// import { Highlight } from '../shared/directives/highlight.directive';
import { SessionService } from '../shared/services/session.service';
import { RestService } from '../shared/services/rest.service';
import { GlobalsService } from '../shared/services/globals.service';
import { Session } from '../shared/classes/session';
import { SessionsDataSource } from '../shared/services/sessions.datasource';

@Component({
  selector: 'app-sessionspanel',
  templateUrl: './sessionspanel.component.html',
  styleUrls: ['./sessionspanel.component.css'],
})
export class SessionspanelComponent implements AfterViewInit, OnInit  {

  // Data source for material design table
  public dataSource: SessionsDataSource;

  @ViewChild(MatPaginator) paginator: MatPaginator;
  @ViewChild(MatSort) sort: MatSort;

  sessions: Session[] = [];
  filteredSessions: Session[] = [];
  errorMessage: string;

  // Data settings for material design table
  public dataSettings: any = {
    pageIndex: 0,
    pageSize: 20,
    query: {},
    sortKey: "last_process",
    sortDirection: "asc",
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
  public asIsSortableColumns = [];

  public asIsNotSortableColumns = [
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

  constructor(private cd: ChangeDetectorRef,
              private globalsService: GlobalsService,
              private restService: RestService,
              private router: Router,
              private sessionService: SessionService) { }

  ngOnInit() {

    // Set up grant table pages
    this.initPagintor();
    this.initSorting();

    // Initialize the data source
    this.dataSource = new SessionsDataSource(this.sessionService);

  }

  ngAfterViewInit() {
    // Load data
    this.loadSessionsPage();
    this.cd.detectChanges();

    // Pagination events
    this.paginator.page
      .pipe(
          tap((event) => {
            this.loadSessionsPage();
            localStorage.setItem("pageSizeSessions", JSON.stringify(event.pageSize));
            localStorage.setItem("pageIndexSessions", JSON.stringify(event.pageIndex));
          })
      )
      .subscribe();

    // Sort evvents
    this.sort.sortChange
      .pipe(
        tap((event) => {
          this.loadSessionsPage();
          localStorage.setItem("sortKeyGrants", JSON.stringify(event.active));
          localStorage.setItem("sortDirectionSessions", JSON.stringify(event.direction));
        })
      )
      .subscribe();
  }

  private loadSessionsPage() {
    this.dataSource.findDocuments(
      {},
      this.sort.active,
      this.sort.direction,
      this.paginator.pageIndex,
      this.paginator.pageSize);
  }

  // getSessions() {
  //   this.restService.getSessions()
  //     .subscribe(
  //      sessions => {
  //        this.filteredSessions = [...sessions];
  //        this.sessions = sessions;
  //       //  console.log(sessions[3]);
  //      },
  //      error => this.errorMessage = (error as any));
  // }

  // Handle a click on the session
  selectSession(event) {

    const id = event.selected[0]._id;

    // Share through globalsService
    this.globalsService.currentSessionId = id;
    this.globalsService.currentSessionType = "mx";

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

  // Initialize the paginator
  private initPagintor() {

    // Set up page size from localStorage
    const maybePageSize = JSON.parse(localStorage.getItem("pageSizeSessions"));
    if (maybePageSize) {
      if (maybePageSize !== this.dataSettings.pageSize) {
        this.dataSettings.pageSize = maybePageSize;
      }
    // Set localStorage to default value
    } else {
      localStorage.setItem("pageSizeSessions", JSON.stringify(this.dataSettings.pageSize));
    }

    // Set up page index from localStorage
    const maybePageIndex = JSON.parse(localStorage.getItem("pageIndexSessions"));
    if (maybePageIndex) {
      if (maybePageIndex !== this.dataSettings.pageIndex) {
        this.dataSettings.pageIndex = maybePageIndex;
      }
    // Set localStorage to default value
    } else {
      localStorage.setItem("pageIndexSessions", JSON.stringify(this.dataSettings.pageIndex));
    }
  }

  private initSorting() {

    // Set sorting
    const maybesortKey = JSON.parse(localStorage.getItem("sortKeySessions"));
    if (maybesortKey) {
      if (maybesortKey !== this.dataSettings.sortKey) {
        this.dataSettings.sortKey = maybesortKey;
      }
    // Set localStorage to default value
    } else {
      localStorage.setItem("sortKeySessions", JSON.stringify(this.dataSettings.sortKey));
    }


    const maybesortDirection = JSON.parse(localStorage.getItem("sortDirectionSessions"));
    if (maybesortDirection) {
      if (maybesortDirection !== this.dataSettings.sortDirection) {
        this.dataSettings.sortDirection = maybesortDirection;
      }
    // Set localStorage to default value
    } else {
      localStorage.setItem("sortDirectionSessions", JSON.stringify(this.dataSettings.sortDirection));
    }
  }

  // Handle a click on a record
  public recordClick(record:any, event:any) {
    const id = record._id;
    this.globalsService.currentSessionId = id;
    this.router.navigate(['/mx', id]);
  }

}
