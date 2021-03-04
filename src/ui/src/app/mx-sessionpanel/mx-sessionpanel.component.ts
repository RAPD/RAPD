import { Component,
         OnInit,
         OnDestroy } from '@angular/core';
import { Router,
         ActivatedRoute,
       /* ROUTER_DIRECTIVES */ } from '@angular/router';

import { MxResultContainerComponent } from './mx-result-container';
import { WebsocketService } from '../shared/services/websocket.service';

@Component({
  selector: 'app-mx-sessionpanel',
  templateUrl: './mx-sessionpanel.component.html',
  styleUrls: ['./mx-sessionpanel.component.css'],
  providers: [ MxResultContainerComponent ]
})
export class MxSessionpanelComponent implements OnInit, OnDestroy {

  public sessionId: string;
  public sub: any;
  public tabsIndexes = [
    'snaps',
    'sweeps',
    'merge',
    'mr',
    'sad',
    'mad'
  ];

  constructor(private router: Router,
              private route: ActivatedRoute,
              private websocketService: WebsocketService) { }

  ngOnInit() {
    this.sub = this.route.params.subscribe(params => {
      // console.log('ngOnInit >>', params);
      this.sessionId = params['session_id'];
      this.websocketService.setSession(this.sessionId, 'mx');
    });
  }

  ngOnDestroy() {
    this.sub.unsubscribe();
    this.websocketService.unsetSession();
    this.websocketService.unsubscribeResults();
  }

  tabSelected(event) {
    // console.log('tab selected', event);
    // console.log('tab=', this.tabs_indexes[event.index]);
    // this.router.navigate(['mx', this.session_id]);
  }
}
