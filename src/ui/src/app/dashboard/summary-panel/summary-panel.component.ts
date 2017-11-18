import { Component,
         OnDestroy,
         OnInit } from '@angular/core';
import { RestService } from '../../shared/services/rest.service';
import { GlobalsService } from '../../shared/services/globals.service';

@Component({
  selector: 'app-summary-panel',
  templateUrl: './summary-panel.component.html',
  styleUrls: ['./summary-panel.component.css']
})
export class SummaryPanelComponent implements OnInit, OnDestroy {

  private error_message:string;
  public results: any[];
  private results_timeout:number;
  public logins: any[];
  private logins_timeout:number;
  public stacked_bar_options:any = {
    layout: {
      padding: {
        left: 10,
        right: 10,
        top: 10,
        bottom: 10
      }
    },
    legend: {
      display: true,
      position: 'right',
      // labels: {
      //   boxWidth: 3,
      // },
    },
    responsive: true,
    scales: {
      xAxes: [{
        stacked: true,
        gridLines: {
          display: false
        },
      }],
      yAxes: [{
        stacked: true,
        gridLines: {
          display: false
        },
      }]
    },
    title:{
      display:false,
      text:"Chart.js Bar Chart - Stacked"
    },
    tooltips: {
      mode: 'index',
      intersect: false
    },
  };
  public colors: any[] = [{backgroundColor:'rgba(256, 0, 0, 1)'},{backgroundColor:'rgba(0, 256, 0, 1)'}];

  constructor(private rest_service: RestService,
              private globals_service: GlobalsService) { }

  ngOnInit() {
    this.getResults();
    this.getLogins();
  }

  getResults() {
    let self = this;
    this.rest_service.getDashboardResults()
      .subscribe(
       results => {
         if (results.success === true) {
           this.results = results.results;
         }
         // console.log(results);
         this.results_timeout = setTimeout(function() {
           self.getResults();
         }, 30000);
       },
       error => this.error_message = <any>error);

  }

  getLogins() {
    let self = this;
    this.rest_service.getDashboardLogins()
      .subscribe(
       results => {
         if (results.success === true) {
           this.logins = results.logins;
         }
         console.log(results.logins);
         this.logins_timeout = setTimeout(function() {
           self.getLogins();
         }, 31000);
       },
       error => this.error_message = <any>error);

  }

  ngOnDestroy() {
    // console.log("DESTROYED");
    clearTimeout(this.results_timeout);
    clearTimeout(this.logins_timeout);
  }
}
