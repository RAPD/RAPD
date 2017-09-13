import { Component, Input, OnInit, OnDestroy } from '@angular/core';

import { ReplaySubject }   from 'rxjs/Rx';

import { WebsocketService } from '../../../shared/services/websocket.service';

@Component({
  selector: 'app-indexstrategy-aaaa-1',
  templateUrl: './indexstrategy-aaaa-1.component.html',
  styleUrls: ['./indexstrategy-aaaa-1.component.css']
})
export class IndexstrategyAaaa1Component implements OnInit, OnDestroy {

  @Input() current_result: any;

  incomingData$: ReplaySubject<string>;

  // lineChart
  public lineChartData: Array<any> = [
    {
      data: [160, 160, 160, 160, 160, 160, 160, 160, 160, 160, 160, 160, 160, 160, 160, 160, 160, 160, 160],
      fill: false,
      label: '3.09Å',
      pointStyle: 'line'
    },
    // {data: [145, 145, 145, 145, 145, 145, 145, 145, 145, 145, 145, 145, 145, 145, 145, 145, 145, 145, 145], label: '3.29Å'},
    // {data: [121, 121, 121, 121, 121, 121, 121, 121, 121, 121, 121, 121, 121, 121, 121, 121, 121, 121, 121], label: '3.49Å'},
  ];
  public lineChartLabels: Array<any> = [0, 20, 40, 60, 80, 100, 120, 140, 160, 180, 200, 220, 240, 260, 280, 300, 320, 340, 360];
  public lineChartOptions: any = {
    animation: false,
    legend: {
      display: true,
      labels: {
        boxWidth: 10,
        usePointStyle: true
      },
      position: 'bottom'
    },
    responsive: true,
    scales: {
      yAxes: [{
        ticks: {
          min: 0
        }
      }]
    },
    title: {
      display: true,
      text: 'Ω Range vs. Start'
    }
  };
  public lineChartColours: Array<any> = [
    { // grey
      backgroundColor: 'rgba(148,159,177,0.2)',
      borderColor: 'rgba(148,159,177,1)',
    },
  ];
  public lineChartLegend: boolean = true;
  public lineChartType: string = 'line';

  // Anomalous
  public lineChartDataAnom: Array<any> = [
    {
      data: [160, 160, 160, 160, 160, 160, 160, 160, 160, 160, 160, 160, 160, 160, 160, 160, 160, 160, 160],
      fill: false,
      label: '3.09Å',
      pointStyle: 'line'
    },
    // {data: [145, 145, 145, 145, 145, 145, 145, 145, 145, 145, 145, 145, 145, 145, 145, 145, 145, 145, 145], label: '3.29Å'},
    // {data: [121, 121, 121, 121, 121, 121, 121, 121, 121, 121, 121, 121, 121, 121, 121, 121, 121, 121, 121], label: '3.49Å'},
  ];
  public lineChartLabelsAnom: Array<any> = [0, 20, 40, 60, 80, 100, 120, 140, 160, 180, 200, 220, 240, 260, 280, 300, 320, 340, 360];
  public lineChartOptionsAnom: any = {
    animation: false,
    legend: {
      display: true,
      labels: {
        boxWidth: 10,
        usePointStyle: true
      },
      position: 'bottom'
    },
    responsive: true,
    scales: {
      yAxes: [{
        ticks: {
          min: 0
        }
      }]
    },
    title: {
      display: true,
      text: 'Ω Range vs. Start'
    }
  };

  constructor(private websocket_service: WebsocketService) { }

  ngOnInit() {
    console.log(this.current_result);
    this.incomingData$ = this.websocket_service.subscribeResultDetails(
      this.current_result.result_type,
      this.current_result.result_id);
    this.incomingData$.subscribe(x => this.handleIncomingData(x));
  }

  ngOnDestroy() {
    console.log('agent ui destroyed');
  }

  public handleIncomingData(data: any) {

    console.log('handleIncomingData', data);

  }

  // events
  public chartClicked(e: any): void {
    console.log(e);
  }

  public chartHovered(e: any): void {
    console.log(e);
  }
}
