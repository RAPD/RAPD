import { Component,
         Input,
         OnInit,
         ViewChild,
         trigger,
         transition,
         style,
         animate } from '@angular/core';
import { MdDialog,
        MD_DIALOG_DATA } from '@angular/material';
import { ReplaySubject }   from 'rxjs/Rx';
// import { BaseChartDirective } from 'ng2-charts';
import { ResultsService } from '../../../shared/services/results.service';

@Component({
  selector: 'app-integrate-bd11-2-0-0',
  templateUrl: './integrate-bd11-2-0-0.component.html',
  styleUrls: ['./integrate-bd11-2-0-0.component.css'],
  animations: [
    trigger(
      'enterAnimation', [
        transition(':enter', [
          style({transform: 'translateX(100%)', opacity: 0}),
          animate('100ms', style({transform: 'translateX(0)', opacity: 1}))
        ]),
        transition(':leave', [
          style({transform: 'translateX(0)', opacity: 1}),
          animate('500ms', style({transform: 'translateX(100%)', opacity: 0}))
        ])
      ]
    )
  ],
})
export class IntegrateBd11200Component implements OnInit {

  objectKeys = Object.keys;
  @Input() current_result: any;
  incomingData$: ReplaySubject<string>;

  full_result: any;
  selected_plot: string;
  data: any;

  // @ViewChild(BaseChartDirective) private _chart;

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
      this.setPlot('Rmerge vs Frame');
    }

    // if ('Imean/RMS scatter' in data.results.plots) {
    //   this.selected_plot = 'Imean/RMS scatter';
    //   this.setPlot('Imean/RMS scatter');
    // }


    console.log(this.selected_plot);
  }

  onPlotSelect(plot_key:string) {

    console.log('onPlotSelect', plot_key);
    // console.log(this.baseChart);
    this.setPlot(plot_key);

  }

  // Set up the plot
  setPlot(plot_key:string) {

    console.log('setPlot', plot_key);

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

      case 'Imean/RMS scatter':
        this.data.xs = this.full_result.results.plots['Imean/RMS scatter'].x_data;
        this.data.ys = this.full_result.results.plots['Imean/RMS scatter'].y_data;
        this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString = this.full_result.results.plots['Imean/RMS scatter'].parameters.ylabel;
        this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = this.full_result.results.plots['Imean/RMS scatter'].parameters.xlabel;
        break;
        // this.data = {
        //   xs: this.full_result.results.plots['Imean/RMS scatter'].x_data,
        //   ys: this.full_result.results.plots['Imean/RMS scatter'].y_data,
        //   lineChartType: 'line',
        //   lineChartOptions: {
        //     animation: {
        //       duration: 500,
        //     },
        //     elements: {
        //       line: {
        //         tension: 0, // disables bezier curves
        //       },
        //     },
        //     legend: {
        //       display: true,
        //       position: 'right',
        //       labels: {
        //         boxWidth: 3,
        //       },
        //     },
        //     responsive: true,
        //     scales: {
        //       yAxes: [{
        //         scaleLabel: {
        //           display: true,
        //           labelString: this.full_result.results.plots['Imean/RMS scatter'].parameters.ylabel,
        //         },
        //         ticks: {
        //           beginAtZero:true
        //         },
        //       }],
        //       xAxes: [{
        //         // afterTickToLabelConversion: function(data){
        //         //       var xLabels = data.ticks;
        //         //
        //         //       xLabels.forEach(function (labels, i) {
        //         //           if (i % 10 !== 0){
        //         //               xLabels[i] = '';
        //         //           }
        //         //       });
        //         //       xLabels.push('360');
        //         // },
        //         scaleLabel: {
        //           display: true,
        //           labelString: this.full_result.results.plots['Imean/RMS scatter'].parameters.xlabel,
        //         },
        //         // ticks: {
        //         //   autoSkipPadding:4
        //         // },
        //       }],
        //     },
        //   },
        // };
        // break;

      case 'Anomalous & Imean CCs vs Resolution':
        this.data.xs = this.full_result.results.plots['Anomalous & Imean CCs vs Resolution'].x_data;
        this.data.ys = this.full_result.results.plots['Anomalous & Imean CCs vs Resolution'].y_data;
        this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString = this.full_result.results.plots['Anomalous & Imean CCs vs Resolution'].parameters.ylabel;
        this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = this.full_result.results.plots['Anomalous & Imean CCs vs Resolution'].parameters.xlabel;

        // this.data = {
        //   xs: this.full_result.results.plots['Anomalous & Imean CCs vs Resolution'].x_data,
        //   ys: this.full_result.results.plots['Anomalous & Imean CCs vs Resolution'].y_data,
        //   lineChartType: 'line',
        //   lineChartOptions: {
        //     animation: {
        //       duration: 500,
        //     },
        //     elements: {
        //       line: {
        //         tension: 0, // disables bezier curves
        //       },
        //     },
        //     legend: {
        //       display: true,
        //       position: 'right',
        //       labels: {
        //         boxWidth: 3,
        //       },
        //     },
        //     responsive: true,
        //     scales: {
        //       yAxes: [{
        //         scaleLabel: {
        //           display: true,
        //           labelString: this.full_result.results.plots['Anomalous & Imean CCs vs Resolution'].parameters.ylabel,
        //         },
        //         ticks: {
        //           beginAtZero:true
        //         },
        //       }],
        //       xAxes: [{
        //         // afterTickToLabelConversion: function(data){
        //         //       var xLabels = data.ticks;
        //         //
        //         //       xLabels.forEach(function (labels, i) {
        //         //           if (i % 10 !== 0){
        //         //               xLabels[i] = '';
        //         //           }
        //         //       });
        //         //       xLabels.push('360');
        //         // },
        //         scaleLabel: {
        //           display: true,
        //           labelString: this.full_result.results.plots['Anomalous & Imean CCs vs Resolution'].parameters.xlabel,
        //         },
        //         // ticks: {
        //         //   autoSkipPadding:4
        //         // },
        //       }],
        //     },
        //   },
        // };
        break;

      case 'RMS correlation ratio':
        this.data.xs = this.full_result.results.plots['RMS correlation ratio'].x_data;
        this.data.ys = this.full_result.results.plots['RMS correlation ratio'].y_data;
        this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString = this.full_result.results.plots['RMS correlation ratio'].parameters.ylabel;
        this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = this.full_result.results.plots['RMS correlation ratio'].parameters.xlabel;
        break;

      case "I/sigma, Mean Mn(I)/sd(Mn(I))":
        this.data.xs = this.full_result.results.plots['I/sigma, Mean Mn(I)/sd(Mn(I))'].x_data;
        this.data.ys = this.full_result.results.plots['I/sigma, Mean Mn(I)/sd(Mn(I))'].y_data;
        this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString = this.full_result.results.plots['I/sigma, Mean Mn(I)/sd(Mn(I))'].parameters.ylabel;
        this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = this.full_result.results.plots['I/sigma, Mean Mn(I)/sd(Mn(I))'].parameters.xlabel;
        break;

      case "rs_vs_res":
        this.data.xs = this.full_result.results.plots['rs_vs_res'].x_data;
        this.data.ys = this.full_result.results.plots['rs_vs_res'].y_data;
        this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString = this.full_result.results.plots['rs_vs_res'].parameters.ylabel;
        this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = this.full_result.results.plots['rs_vs_res'].parameters.xlabel;
        break;

      default:
        this.data = false;
    }
  }

}
