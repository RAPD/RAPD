import {CollectionViewer, DataSource} from "@angular/cdk/collections";
import {Observable, BehaviorSubject, of} from "rxjs";
import {Session} from "../classes/session";
import {SessionService} from "./session.service";
import {catchError, finalize} from "rxjs/operators";



export class SessionsDataSource implements DataSource<Session> {

    private sessionsSubject = new BehaviorSubject<Session[]>([]);

    private loadingSubject = new BehaviorSubject<boolean>(false);

    public loading$ = this.loadingSubject.asObservable();

    constructor(private sessionService: SessionService) {

    }

    loadSessions(_id:string,
                filter:string,
                sortDirection:string,
                pageIndex:number,
                pageSize:number) {

        this.loadingSubject.next(true);

        this.sessionService.findSessions(_id, filter, sortDirection,
            pageIndex, pageSize).pipe(
                catchError(() => of([])),
                finalize(() => this.loadingSubject.next(false))
            )
            .subscribe(sessions => this.sessionsSubject.next(sessions));

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
