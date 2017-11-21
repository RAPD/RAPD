import { Component,
         OnDestroy,
        OnInit } from '@angular/core';
import { RestService } from '../../shared/services/rest.service';
import { GlobalsService } from '../../shared/services/globals.service';

@Component({
  selector: 'app-activities-panel',
  templateUrl: './activities-panel.component.html',
  styleUrls: ['./activities-panel.component.css']
})
export class ActivitiesPanelComponent implements OnInit {

  private error_message:string;
  public  server_activities: any;
  private server_activities_timeout:number;
  public line_options:any = {
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
      position: 'right'
    },
    responsive: true,
    scales: {
      xAxes: [{
        // stacked: true,
        gridLines: {
          display: false
        },
      }],
      yAxes: [{
        // stacked: true,
        gridLines: {
          display: true
        },
      }]
    },
    title:{
      display:false,
      text:"Chart.js Bar Chart - Stacked"
    },
    tooltips: {
      mode: 'index',
      intersect: true
    },
  };
  public colors = [{
    backgroundColor:'rgb(255, 159, 64)',
    borderColor:'rgb(255, 159, 64)'
    },
    {
    backgroundColor:'rgb(54, 162, 235)',
    borderColor:'rgb(54, 162, 235)'
    }]

  constructor(private rest_service: RestService,
              private globals_service: GlobalsService) { }

  ngOnInit() {
    this.getServerActivities();
  }

  getServerActivities() {
    let self = this;
    this.rest_service.getServerActivities()
      .subscribe(
       results => {
         if (results.success === true) {
           this.server_activities = results.activities;
         }
         // console.log(results);
         this.server_activities_timeout = setTimeout(function() {
           self.getServerActivities();
         }, 30000);
       },
       error => this.error_message = <any>error);
  }

  ngOnDestroy() {
    // console.log("DESTROYED");
    clearTimeout(this.server_activities_timeout);
  }
}
