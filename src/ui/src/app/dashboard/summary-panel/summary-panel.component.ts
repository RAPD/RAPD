import { Component,
         OnInit } from '@angular/core';
import { RestService } from '../../shared/services/rest.service';

@Component({
  selector: 'app-summary-panel',
  templateUrl: './summary-panel.component.html',
  styleUrls: ['./summary-panel.component.css']
})
export class SummaryPanelComponent implements OnInit {

  private error_message:string;
  public results: any[];
  public stacked_bar_options:any = {
    title:{
      display:true,
      text:"Chart.js Bar Chart - Stacked"
    },
    tooltips: {
      mode: 'index',
      intersect: false
    },
    responsive: true,
    scales: {
      xAxes: [{
        stacked: true,
      }],
      yAxes: [{
        stacked: true
      }]
    }
  }

  constructor(private rest_service: RestService) { }

  ngOnInit() {
    this.getResults();
  }

  getResults() {

    this.rest_service.getDashboardResults()
      .subscribe(
       results => {
         if (results.success === true) {
           this.results = results.results;
         }
         console.log(results);
         // this.update_timeout = setTimeout(function() {
         //   self.getOverwatches();
         // }, 10000);
       },
       error => this.error_message = <any>error);

  }

}
