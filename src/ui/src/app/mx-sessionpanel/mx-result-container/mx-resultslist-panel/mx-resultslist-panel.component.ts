import { Component,
         OnInit,
         Input,
         Output,
         EventEmitter } from '@angular/core';
import { ReplaySubject } from 'rxjs/Rx';
import { Highlight } from '../../../shared/directives/highlight.directive';
import { ResultsService } from '../../../shared/services/results.service';

@Component({
  selector: 'app-mx-resultslist-panel',
  templateUrl: './mx-resultslist-panel.component.html',
  styleUrls: ['./mx-resultslist-panel.component.css'],
})
export class MxResultslistPanelComponent implements OnInit {

  highlight_color = 'white';
  message: string;

  // The currently active result
  active_result: string;

  // Arrays for holding result thumbnail data structures
  data_results: Array<any> = [];
  data_results_object: any = {};
  index_results: Array<any> = [];
  integrate_results: Array<any> = [];
  merge_results: Array<any> = [];
  mr_results: Array<any> = [];
  sad_results: Array<any> = [];
  mad_results: Array<any> = [];

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

  constructor(private results_service: ResultsService) { }

  ngOnInit() {
    this.incomingData$ = this.results_service.subscribeResults(this.session_id);
    this.incomingData$.subscribe(x => this.handleIncomingData(x));
  }

  private handleIncomingData(data: any) {
    let self = this;
    if (data.msg_type === 'results') {
      for (let result of data.results) {
        if (result.result_type === this.result_types[this.result_type]) {
          console.log(result);
          // New result
          let id = result._id; // result.process.process_id;
          if (self.data_results.indexOf(id) === -1) {
            self.data_results.push(id);
          }
          self.data_results_object[id] = result;
        }

        // if (result.result_type === 'mx:index+strategy') {
        //   self.index_results.push(result);
        // } else if (result.result_type === 'mx:integrate') {
        //   self.integrate_results.push(result);
        // }
      }
    }
  }

  private onClick(id: string) {
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
}
