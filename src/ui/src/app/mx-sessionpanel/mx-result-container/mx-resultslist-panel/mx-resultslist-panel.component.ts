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

  // index_results: Array<any> = [];
  // integrate_results: Array<any> = [];
  // merge_results: Array<any> = [];
  // mr_results: Array<any> = [];
  // sad_results: Array<any> = [];
  // mad_results: Array<any> = [];

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

    console.log(data);

    // if (data.msg_type === 'results') {
    for (let result of data) {
        if ((result.data_type+':'+result.plugin_type).toLowerCase() === this.result_types[this.result_type]) {
          console.log(result);

          // Filter for age/display
          let disp:string = result.display;
          if (! disp in {pinned:1, trashed:1}) {
            if (result.status < 100) {
              let result_time:any = new Date(result.timestamp);
              if (Date.now() - result_time > 3600) {
                return false;
              }
            }
          }

          // New result
          let id = result._id; // result.process.process_id;
          console.log(id);
          console.log(self.data_results);
          if (self.data_results.indexOf(id) === -1) {
            console.log('new');
            self.data_results.unshift(id);
          }
          self.data_results_object[id] = result;
        }

        // if (result.result_type === 'mx:index+strategy') {
        //   self.index_results.push(result);
        // } else if (result.result_type === 'mx:integrate') {
        //   self.integrate_results.push(result);
        // }
      }
    // }
  }

  private onClick(id: string):void {
    console.log(id);
    // console.log(event);
    // event.target

    // Save the current result as the active result
    this.active_result = id;

    // Use the result to call for full results
    this.resultSelect.emit({
      value: this.data_results_object[id]
    });
  }

  // Should the result be in the list?
  // public shouldDisplay(id:string): boolean {
  //
  //   // console.log('display', id);
  //
  //   let result = this.data_results_object[id];
  //   // console.log(result.status, result.timestamp);
  //   if (result.display in {pinned:1, trashed:1}) {
  //     return false;
  //   } else if (result.status == 100) {
  //     return true;
  //   }  else {
  //     let d:any = new Date(result.timestamp);
  //     if (Date.now() - d < 3600) {
  //       // console.log('  new enough');
  //       return true;
  //     } else {
  //       // console.log('  too old');
  //       return false;
  //     }
  //   }

    // if (result.status === 100 || (Date.now() - d) < 36000) {
    //   if (result.display) {
    //     return result.display;
    //   } else {
    //     return 'normal';
    //   }
    // } else {
    //   return '';
    // }
    //
    // if ((Date.now() - timestamp) > 3600 ) {
    //   return true;
    // } else {
    //   return false;
    // }
  // }
}
