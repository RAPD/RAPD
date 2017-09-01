import { Component,
         Input,
         OnInit } from '@angular/core';
import { MdDialog,
        MD_DIALOG_DATA } from '@angular/material';
import { ReplaySubject }   from 'rxjs/Rx';
import { ResultsService } from '../../../shared/services/results.service';

@Component({
  selector: 'app-integrate-bd11-2-0-0',
  templateUrl: './integrate-bd11-2-0-0.component.html',
  styleUrls: ['./integrate-bd11-2-0-0.component.css']
})
export class IntegrateBd11200Component implements OnInit {

  objectKeys = Object.keys;
  @Input() current_result: any;
  incomingData$: ReplaySubject<string>;

  full_result: any;
  selected_plot: string;
  data: any;

  constructor(private results_service: ResultsService,
              public dialog: MdDialog) { }

  ngOnInit() {
    // Subscribe to results for the displayed result
    this.incomingData$ = this.results_service.subscribeResultDetails(
      this.current_result.result_type,
      this.current_result.result_id);
    this.incomingData$.subscribe(x => this.handleIncomingData(x));
  }

  // lineChart
  public lineChartOptions:any = {
    responsive: true,
    legend: {
      display: true,
      position: 'right',
    }
  };
  public lineChartColors:Array<any> = [
    { // green
      backgroundColor: 'rgba(0,0,0,0)',
      borderColor: 'rgba(0, 128, 128, 1)',
      pointBackgroundColor: 'rgba(0, 128, 128, 1)',
      pointBorderColor: 'rgba(0, 128, 128, 1)',
      pointHoverBackgroundColor: 'rgba(0, 128, 128, 1)',
      pointHoverBorderColor: 'rgba(0, 128, 128, 1)'
    },
    { // dark grey
      backgroundColor: 'rgba(0,0,0,0)',
      borderColor: 'rgba(122, 198, 150, 1)',
      pointBackgroundColor: 'rgba(122, 198, 150, 1)',
      pointBorderColor: 'rgba(122, 198, 150, 1)',
      pointHoverBackgroundColor: 'rgba(122, 198, 150, 1)',
      pointHoverBorderColor: 'rgba(122, 198, 150, 1)'
    },
    { // grey
      backgroundColor: 'rgba(0,0,0,0)',
      borderColor: 'rgba(125, 125, 114, 1)',
      pointBackgroundColor: 'rgba(125, 125, 114, 1)',
      pointBorderColor: 'rgba(125, 125, 114, 1)',
      pointHoverBackgroundColor: 'rgba(125, 125, 114, 1)',
      pointHoverBorderColor: 'rgba(125, 125, 114, 1)'
    },
    { // grey
      backgroundColor: 'rgba(0,0,0,0)',
      borderColor: 'rgba(239, 115, 139, 1)',
      pointBackgroundColor: 'rgba(239, 115, 139, 1)',
      pointBorderColor: 'rgba(239, 115, 139, 1)',
      pointHoverBackgroundColor: 'rgba(239, 115, 139, 1)',
      pointHoverBorderColor: 'rgba(239, 115, 139, 1)'
    },
    { // grey
      backgroundColor: 'rgba(0,0,0,0)',
      borderColor: 'rgba(139, 0, 0, 1)',
      pointBackgroundColor: 'rgba(139, 0, 0, 1)',
      pointBorderColor: 'rgba(139, 0, 0, 1)',
      pointHoverBackgroundColor: 'rgba(139, 0, 0, 1)',
      pointHoverBorderColor: 'rgba(139, 0, 0, 1)'
    }
  ];
  public lineChartLegend:boolean = true;
  public lineChartType:string = 'line';

  public handleIncomingData(data: any) {
    console.log('handleIncomingData', data);
    this.full_result = data;

    // Select the default plot to show
    if ('Rmerge vs Frame' in data.results.plots) {
      this.selected_plot = 'Rmerge vs Frame';
      this.data = {
        xs: this.full_result.results.plots['Rmerge vs Frame'].x_data,
        ys: this.full_result.results.plots['Rmerge vs Frame'].y_data,
        lineChartType: 'line',
        lineChartOptions: {
          animation: {
            duration: 500,
          },
          elements: {
            line: {
              tension: 0, // disables bezier curves
            },
          },
          legend: {
            display: true,
            position: 'right',
            labels: {
              boxWidth: 3,
            },
          },
          responsive: true,
          scales: {
            yAxes: [{
              scaleLabel: {
                display: true,
                labelString: this.full_result.results.plots['Rmerge vs Frame'].parameters.ylabel,
              },
              ticks: {
                beginAtZero:true
              },
            }],
            xAxes: [{
              // afterTickToLabelConversion: function(data){
              //       var xLabels = data.ticks;
              //
              //       xLabels.forEach(function (labels, i) {
              //           if (i % 10 !== 0){
              //               xLabels[i] = '';
              //           }
              //       });
              //       xLabels.push('360');
              // },
              scaleLabel: {
                display: true,
                labelString: this.full_result.results.plots['Rmerge vs Frame'].parameters.xlabel,
              },
              // ticks: {
              //   autoSkipPadding:4
              // },
            }],
          },

        },
      };
    }

    console.log(this.selected_plot);
  }

  onPlotSelect(plot_key:string) {

    console.log('onPlotSelect', plot_key);

    this.setPlot(plot_key);

  }

  // Set up the plot
  setPlot(plot_key:string) {

    switch (plot_key) {

      case 'Rmerge vs Frame':
        this.data = {
          xs: this.full_result.results.plots['Rmerge vs Frame'].x_data,
          ys: this.full_result.results.plots['Rmerge vs Frame'].y_data,
          lineChartType: 'line',
          lineChartOptions: {
            animation: {
              duration: 500,
            },
            elements: {
              line: {
                tension: 0, // disables bezier curves
              },
            },
            legend: {
              display: true,
              position: 'right',
              labels: {
                boxWidth: 3,
              },
            },
            responsive: true,
            scales: {
              yAxes: [{
                scaleLabel: {
                  display: true,
                  labelString: this.full_result.results.plots['Rmerge vs Frame'].parameters.ylabel,
                },
                ticks: {
                  beginAtZero:true
                },
              }],
              xAxes: [{
                // afterTickToLabelConversion: function(data){
                //       var xLabels = data.ticks;
                //
                //       xLabels.forEach(function (labels, i) {
                //           if (i % 10 !== 0){
                //               xLabels[i] = '';
                //           }
                //       });
                //       xLabels.push('360');
                // },
                scaleLabel: {
                  display: true,
                  labelString: this.full_result.results.plots['Rmerge vs Frame'].parameters.xlabel,
                },
                // ticks: {
                //   autoSkipPadding:4
                // },
              }],
            },
          },
        };
        break;

      default:
        this.data = false;
    }
  }

}
