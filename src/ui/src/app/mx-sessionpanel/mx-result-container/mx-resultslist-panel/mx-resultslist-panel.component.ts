import { Component,
        //  OnDestroy,
         OnInit,
         Input,
         Output,
         Pipe,
         PipeTransform,
         EventEmitter } from '@angular/core';
import { ReplaySubject } from 'rxjs/Rx';
import { Highlight } from '../../../shared/directives/highlight.directive';
import { WebsocketService } from '../../../shared/services/websocket.service';
import { ArraySortPipe } from '../../../shared/pipes/array-sort.pipe';

@Component({
  selector: 'app-mx-resultslist-panel',
  templateUrl: './mx-resultslist-panel.component.html',
  styleUrls: ['./mx-resultslist-panel.component.css'],
  pipes: [ ArraySortPipe ],
})
export class MxResultslistPanelComponent implements OnInit /*, OnDestroy*/ {

  highlight_color = 'white';
  message: string;

  // The currently active result
  active_result: string;

  // Arrays for holding result thumbnail data structures
  data_results: Array<any> = [];
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

        console.log('Adding to', this.result_types[this.result_type], 'results');

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
        // if (self.data_results_ids.indexOf(result._id) === -1) {
        //   self.data_results_ids.unshift(result._id);
        // }

        // Look for index of result
        var index = this.data_results.findIndex(function(elem) {
          if (elem._id === result._id) {
            return true;
          } else {
            return false;
          }
        });
        // Update
        console.log('  index:', index);
        if (index !== -1) {
          console.log('  Updated data');
          this.data_results[index] = result;
        // Insert
        } else {
          console.log('  New data');
          this.data_results.unshift(result);
        }

        // Update parent objects
        if (result.parent_id) {
          console.log('Have parent_id', result.parent_id);
          var parent_result = this.getResult(result.parent_id);
          if (parent_result) {
            console.log('parent_result:', parent_result);
            // Look for index of result
            var index = parent_result.children.findIndex(function(elem) {
              if (elem._id === result._id) {
                return true;
              } else {
                return false;
              }
            });
            // Update
            console.log('  index:', index);
            if (index !== -1) {
              console.log('  Updated data');
              parent_result[index] = result;
            // Insert
            } else {
              console.log('  New data');
              parent_result.unshift(result);
            }
          }
        }

        // Update children
        console.log('result.children');
        if (result.children != false); {
          console.log('Have children', result.children);
          result.children.forEach(function(elem, index) {
            console.log('  child:', elem);
            var child_result = self.getResult(elem);
            console.log('  child_result:', child_result);
            result.children[index] = child_result;
          });
        }

        // Update results
        // self.data_results_object[result._id] = result;
        // }
    }

    // Sort the data array
    this.data_results.sort(function(a, b) {
        if (a.timestamp > b.timestamp) {
          return -1;
        } else if (a.timestamp < b.timestamp) {
          return 1;
        } else {
          return 0;
        }

    });
  }

  private getResult(id:string) {
    return this.data_results.find(function(elem) {
      if (elem._id === id) {
        return true;
      } else {
        return false;
      }
    });
  }

  private onClick(id:string) {

    console.log('onClick', id);

    // Save the current result as the active result
    this.active_result = id;

    // Use the result to call for full results
    this.resultSelect.emit({
      value: this.getResult(id)
    });
  }
}
