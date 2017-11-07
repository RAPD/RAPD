import { Component,
        //  OnDestroy,
         OnInit,
         Input,
         Output,
         EventEmitter } from '@angular/core';
import { ReplaySubject } from 'rxjs/Rx';
import { Highlight } from '../../../shared/directives/highlight.directive';
import { WebsocketService } from '../../../shared/services/websocket.service';

@Component({
  selector: 'app-mx-resultslist-panel',
  templateUrl: './mx-resultslist-panel.component.html',
  styleUrls: ['./mx-resultslist-panel.component.css'],
})
export class MxResultslistPanelComponent implements OnInit /*, OnDestroy*/ {

  highlight_color = 'white';
  message: string;

  // The currently active result
  active_result: string;

  // Arrays for holding result thumbnail data structures
  data_results_ids: Array<any> = [];
  data_results_object: any = {};

  // Object for holding progressbar counters
  progressbar_counters:any = {};

  incomingData$: ReplaySubject<string>;

  result_types = {
    snap: 'mx:index',
    sweep: 'mx:integrate',
    merge: 'mx:merge',
    mr: 'mx:mr',
    sad: 'mx:sad',
    mad: 'mx:mad'
  }

  @Input() session_id: string;
  @Input() result_type: string;
  @Output() resultSelect = new EventEmitter();

  constructor(private websocket_service: WebsocketService) { }

  ngOnInit() {
    this.incomingData$ = this.websocket_service.subscribeResults(this.session_id);
    this.incomingData$.subscribe(x => this.handleIncomingData(x));
  }

  // ngOnDestroy() {
  //   this.sub.unsubscribe();
  // }

  private handleIncomingData(data: any) {

    let self = this;

    for (let result of data) {
      // My kind of data
      if ((result.data_type+':'+result.plugin_type).toLowerCase() === this.result_types[this.result_type]) {

        // Filter for age & status
        if (! result.display) {
          if (result.status > 0 && result.status < 100) {
            let result_time:any = Date.parse(result.timestamp);
            if (Date.now() - result_time > 3600000) {
              return false;
            }
          }
        }

        // Add to result list
        if (self.data_results_ids.indexOf(result._id) === -1) {
          self.data_results_ids.unshift(result._id);
        }

        // Update results
        self.data_results_object[result._id] = result;
      }
    }

    // Sort the data array
    this.data_results_ids.sort(function(a, b) {
      return self.data_results_object[a].timestamp - self.data_results_object[b].timestamp;
    });

  }

  private onClick(id:string):void {

    // Save the current result as the active result
    this.active_result = id;

    // Use the result to call for full results
    this.resultSelect.emit({
      value: this.data_results_object[id]
    });
  }
}
