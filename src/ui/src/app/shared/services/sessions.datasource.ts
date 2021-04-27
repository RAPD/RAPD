import { CollectionViewer, DataSource } from "@angular/cdk/collections";
import { Observable, BehaviorSubject, of } from "rxjs";
import { Session } from "../classes/session";
import { SessionService } from "./session.service";
import { catchError, finalize } from "rxjs/operators";


export class SessionsDataSource implements DataSource<Session> {

    private sessionsSubject = new BehaviorSubject<Session[]>([]);
    private loadingSubject = new BehaviorSubject<boolean>(false);
    private countSubject = new BehaviorSubject<any>(0);

    public loading$ = this.loadingSubject.asObservable();
    public count$ = this.countSubject.asObservable();

    constructor(private sessionService: SessionService) { }

    findDocuments(query:any={},
                  sortKey:string='',
                  sortDirection:string='asc',
                  pageIndex:number=0,
                  pageSize:number=20) {

      const skip = pageIndex * pageSize;

      this.loadingSubject.next(true);

      this.sessionService.findDocuments(query, sortKey, sortDirection, skip, pageSize).pipe(
            catchError(() => of([])),
            finalize(() => this.loadingSubject.next(false))
        )
        .subscribe(sessions => this.sessionsSubject.next(sessions));

      this.sessionService.countDocuments(query).pipe(
        catchError(() => of([])),
      )
      .subscribe(count => {
        // console.debug(count);
        this.countSubject.next(count);
      });

    }

    connect(collectionViewer: CollectionViewer): Observable<Session[]> {
        console.log("Connecting data source");
        return this.sessionsSubject.asObservable();
    }

    disconnect(collectionViewer: CollectionViewer): void {
        this.sessionsSubject.complete();
        this.loadingSubject.complete();
    }

}
