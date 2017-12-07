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

  public session_id: string;
  public sub: any;
  public tabs_indexes = [
    'snaps',
    'sweeps',
    'merge',
    'mr',
    'sad',
    'mad'
  ];

  constructor(private router: Router,
              private route: ActivatedRoute,
              private websocket_service: WebsocketService) { }

  ngOnInit() {
    this.sub = this.route.params.subscribe(params => {
      console.log('ngOnInit >>', params);
      this.session_id = params['session_id'];
      this.websocket_service.setSession(this.session_id, 'mx');
    });
  }

  ngOnDestroy() {
    this.sub.unsubscribe();
  }

  tabSelected(event) {
    console.log('tab selected', event);
    console.log('tab=', this.tabs_indexes[event.index]);
    // this.router.navigate(['mx', this.session_id]);
  }
}
