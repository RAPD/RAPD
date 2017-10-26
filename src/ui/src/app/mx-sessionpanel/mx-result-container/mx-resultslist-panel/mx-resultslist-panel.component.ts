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
  data_results: Array<any> = [];
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

        // Is this a child?
        // if (result.parent_id) {
        //   console.log('Have parent');

        //   // If the result is pinned or junked, it is de-parented
        //   if (! (result.display === 'junked' || result.display === 'pinned')) {
        //
        //     console.log('Not junked or pinned');
        //
        //     // Parent is here
        //     let parent_index = self.data_results.indexOf(result.parent_id);
        //     if (parent_index !== -1) {
        //       console.log('parent is here');
        //       // Make sure it's on the children list
        //       if (self.data_results_object[result.parent_id].children.indexOf(result._id) === -1) {
        //         console.log('Adding self to list');
        //         self.data_results_object[result.parent_id].children.unshift(result._id);
        //       }
        //     }
        //     // Make sure it's not already on the normal list
        //     let present = self.data_results.indexOf(result._id);
        //     if (present !== -1) {
        //       self.data_results.splice(present, 1);
        //     }
        //   // Child, but junked or pinned
        //   } else {
        //     // Make sure it's on the main list
        //     if (self.data_results.indexOf(result._id) === -1) {
        //       self.data_results.unshift(result._id);
        //     }
        //     // Make sure it's not on the parent
        //     // Parent is here
        //     let index = self.data_results.indexOf(result.parent_id);
        //     if (index !== -1) {
        //       // Make sure it's on the children list
        //       let present = self.data_results_object[result.parent_id].children.indexOf(result._id);
        //       if (present !== -1) {
        //         self.data_results_object[result.parent_id].children.splice(present, 1);
        //       }
        //     }
        //   }
        // // Not a child, so make sure there is a children array
        // } else {
        //   if (result.children === undefined) {
        //     result.children = [];
        //   }
        //   // Not a child at all
        //   if (self.data_results.indexOf(result._id) === -1) {
        //     self.data_results.unshift(result._id);
        //   }
        // }

        // Add to result list
        if (self.data_results.indexOf(result._id) === -1) {
          self.data_results.unshift(result._id);
        }

        // Update results
        self.data_results_object[result._id] = result;
      }
    }
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
