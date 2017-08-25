import { Component,
         Input,
         OnDestroy,
         OnInit } from '@angular/core';
import { MdDialog,
         MD_DIALOG_DATA } from '@angular/material';
import { ReplaySubject }   from 'rxjs/Rx';
import { ResultsService } from '../../../shared/services/results.service';
import { PlotOmegaStartComponent } from './plot-omega-start/plot-omega-start.component'

@Component({
  selector: 'app-index-3b34-2-0-0',
  templateUrl: './index-3b34-2-0-0.component.html',
  styleUrls: ['./index-3b34-2-0-0.component.css']
})
export class Index3b34200Component implements OnInit {

  @Input() current_result: any;
  full_result: any;

  incomingData$: ReplaySubject<string>;

  constructor(private results_service: ResultsService,
              public dialog: MdDialog) { }

  ngOnInit() {
    // console.log(this.current_result);
    this.incomingData$ = this.results_service.subscribeResultDetails(
      this.current_result.result_type,
      this.current_result.result_id);
    this.incomingData$.subscribe(x => this.handleIncomingData(x));
  }

  ngOnDestroy() {
    console.log('agent ui destroyed');
  }

  public handleIncomingData(data: any) {
    console.log('handleIncomingData', data);
    this.full_result = data;
  }

  plotOmegaStartNorm(event) {

    console.log(this.full_result.results.plots.osc_range)

    let config = {
      width: '800px',
      height: '800px',
      data: {
        dialog_title: 'Starting Point',
        ys: this.full_result.results.plots.osc_range.y_data.map(function(el) {
          var o = Object.assign({}, el);
          console.log(o);
          o.pointRadius = 0;
          o.backgroundColor = 'rgba(0,0,0,0)';
          return o;
        }),
        xs: this.full_result.results.plots.osc_range.x_data,
        lineChartType: 'line',
        lineChartOptions: {
          responsive: true,
          // colors: {
          //    backgroundColor: 'rgba(0,0,0,0)',
          // },
          legend: {
            display: true,
            position: 'right',
            labels: {
              boxWidth: 20,
            },
          },
          scales: {
            yAxes: [{
              ticks: {
                beginAtZero:true
              },
            }],
            xAxes: [{
              ticks: {
                autoSkipPadding:4
              },
            }],
          },
        },
      },
    };
    let dialogRef = this.dialog.open(PlotOmegaStartComponent, config);
  }
}
