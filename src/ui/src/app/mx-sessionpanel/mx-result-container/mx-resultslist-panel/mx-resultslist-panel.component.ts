import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';

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

  // Arrays for holding result thumbnail data structures
  data_results: Array<any> = [];
  index_results: Array<any> = [];
  integrate_results: Array<any> = [];
  merge_results: Array<any> = [];
  mr_results: Array<any> = [];
  sad_results: Array<any> = [];
  mad_results: Array<any> = [];

  incomingData$: ReplaySubject<string>;

  result_types = {
    snap: 'mx:index+strategy',
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
        console.log(result);
        if (result.result_type === this.result_types[this.result_type]) {
          self.data_results.push(result);
        }

        // if (result.result_type === 'mx:index+strategy') {
        //   self.index_results.push(result);
        // } else if (result.result_type === 'mx:integrate') {
        //   self.integrate_results.push(result);
        // }
      }
    }
  }

  private onClick(result: any) {
    console.log(result);
    this.resultSelect.emit({
      value: result
    });
  }
}
