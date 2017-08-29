import { Component,
         Input,
         OnDestroy,
         OnInit,
         Pipe,
         PipeTransform } from '@angular/core';
import { MdDialog,
         MD_DIALOG_DATA,
         MdSnackBar } from '@angular/material';
import { ReplaySubject }   from 'rxjs/Rx';
import { ResultsService } from '../../../shared/services/results.service';
import { PlotOmegaStartComponent } from './plot-omega-start/plot-omega-start.component';
import { HeaderDialogComponent } from './header-dialog/header-dialog.component';
import { ReindexDialogComponent } from './reindex-dialog/reindex-dialog.component';

@Component({
  selector: 'app-index-3b34-2-0-0',
  templateUrl: './index-3b34-2-0-0.component.html',
  styleUrls: ['./index-3b34-2-0-0.component.css']
})
export class Index3b34200Component implements OnInit {

  @Input() current_result: any;
  full_result: any;
  index_result: any;

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

    this.index_result = [{
      spacegroup: this.full_result.results.labelit_results.best_sym,
      unit_cell: this.full_result.results.labelit_results.best_cell,
      mosaicity: this.full_result.results.labelit_results.mosflm_mos[0],
      resolution: this.full_result.results.labelit_results.mosflm_res[0],
    },];
  }

  // Display the header information
  displayHeader(header) {

    let config = {
      width: '450px',
      height: '500px',
      data: header };

    let dialogRef = this.dialog.open(HeaderDialogComponent, config);
  }

  plotOmegaStart(mode) {

    if (mode === 'norm') {
      var tag = 'NORMAL',
          y_data = this.full_result.results.plots.osc_range.y_data,
          x_data = this.full_result.results.plots.osc_range.x_data;
    } else {
      var tag = 'ANOMALOUS',
          y_data = this.full_result.results.plots.osc_range_anom.y_data,
          x_data = this.full_result.results.plots.osc_range_anom.x_data;
    }

    let config = {
      width: '800px',
      height: '475px',
      data: {
        dialog_title: 'Sweep Width to Achieve Completeness - '+tag,
        ys: y_data.slice(0,5).map(function(el) {
          var o = Object.assign({}, el);
          o.pointRadius = 0;
          o.backgroundColor = 'rgba(0,0,0,0)';
          // o.showLine = false;
          return o;
        }),
        xs: x_data,
        lineChartType: 'line',
        lineChartOptions: {
          animation: {
            duration: 500,
          },
          responsive: true,
          legend: {
            display: true,
            position: 'right',
            labels: {
              boxWidth: 3,
            },
          },
          scales: {
            yAxes: [{
              scaleLabel: {
                display: true,
                labelString: 'Required Sweep Width',
              },
              ticks: {
                beginAtZero:true
              },
            }],
            xAxes: [{
              afterTickToLabelConversion: function(data){
                    var xLabels = data.ticks;

                    xLabels.forEach(function (labels, i) {
                        if (i % 10 !== 0){
                            xLabels[i] = '';
                        }
                    });
                    xLabels.push('360');
              },
              scaleLabel: {
                display: true,
                labelString: 'Starting Omega',
              },
              // ticks: {
              //   autoSkipPadding:4
              // },
            }],
          },
          tooltips: {
            callbacks: {
              label: function(tooltipItem, data) {
                return tooltipItem.yLabel+'° width';
              },
              title: function(tooltipItem, data) {
                console.log(tooltipItem);
                console.log(data);
                return data.labels[tooltipItem[0].index]+'° start';
              },
            },
          },
        },
      },
    };
    let dialogRef = this.dialog.open(PlotOmegaStartComponent, config);
  }

  plotDeltaOmega(mode) {

    console.log(this.full_result.results.plots);

    let x_data = this.full_result.results.plots.max_delta_omega.x_data,
        y_data = this.full_result.results.plots.max_delta_omega.y_data;

    let config = {
      width: '800px',
      height: '475px',
      data: {
        dialog_title: 'Max Delta Omega With No Overlaps',
        ys: y_data.slice(0,5).map(function(el) {
          var o = Object.assign({}, el);
          o.pointRadius = 0;
          o.backgroundColor = 'rgba(0,0,0,0)';
          // o.showLine = false;
          return o;
        }),
        xs: x_data,
        lineChartType: 'line',
        lineChartOptions: {
          animation: {
            duration: 500,
          },
          responsive: true,
          legend: {
            display: true,
            position: 'right',
            labels: {
              boxWidth: 3,
            },
          },
          scales: {
            yAxes: [{
              scaleLabel: {
                display: true,
                labelString: 'Omega Step',
              },
              ticks: {
                beginAtZero:true
              },
            }],
            xAxes: [{
              afterTickToLabelConversion: function(data){
                    var xLabels = data.ticks;

                    xLabels.forEach(function (labels, i) {
                        if (i % 10 !== 0){
                            xLabels[i] = '';
                        }
                    });
                    xLabels.push('180');
              },
              scaleLabel: {
                display: true,
                labelString: 'Omega',
              },
              // ticks: {
              //   autoSkipPadding:4
              // },
            }],
          },
          tooltips: {
            callbacks: {
              label: function(tooltipItem, data) {
                return tooltipItem.yLabel+'° step';
              },
              title: function(tooltipItem, data) {
                console.log(tooltipItem);
                console.log(data);
                return data.labels[tooltipItem[0].index]+'°';
              },
            },
          },
        },
      },
    };
    let dialogRef = this.dialog.open(PlotOmegaStartComponent, config);
  }

  openReindexDialog() {
    let config = {
      height: '800px',
      width: '500px',
      data: this.full_result
    };

    let dialogRef = this.dialog.open(ReindexDialogComponent, config);
  }

}
/*
 * Raise the value exponentially
 * Takes an exponent argument that defaults to 1.
 * Usage:
 *   value | exponentialStrength:exponent
 * Example:
 *   {{ 2 | exponentialStrength:10 }}
 *   formats to: 1024
*/
// @Pipe({name: 'fullToIndexResult'})
// export class FullToIndexResultPipe implements PipeTransform {
//   transform(full_result: any): any {
//     return [{
//       spacegroup: full_result.results.labelit_results.best_sym,
//       unit_cell: full_result.results.labelit_results.best_cell,
//       mosaicity: full_result.results.labelit_results.mosflm_mos[0],
//       resolution: full_result.results.labelit_results.mosflm_res[0]
//     }];
//   }
// }
