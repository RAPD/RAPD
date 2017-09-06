import { Component,
         Input,
         OnInit } from '@angular/core';

@Component({
  selector: 'app-analysis-f068-2-0-0',
  templateUrl: './analysis-f068-2-0-0.component.html',
  styleUrls: ['./analysis-f068-2-0-0.component.css']
})
export class AnalysisF068200Component implements OnInit {

  @Input() result: any;
  objectKeys = Object.keys;
  selected_plot: string;
  data: any;

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

  constructor() { }

  ngOnInit() {

    console.log(this.result);

    if ('Intensity plots' in this.result.parsed.xtriage.plots) {
      this.selected_plot = 'Intensity plots';
      this.setPlot('Intensity plots')
    }

  }

  setPlot(plot_key:string) {

    console.log('setPlot', plot_key);

    switch (plot_key) {

      case 'Intensity plots':
        this.data = {
          xs: this.result.parsed.xtriage.plots[plot_key].x_data,
          ys: this.result.parsed.xtriage.plots[plot_key].y_data,
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
                  labelString: this.result.parsed.xtriage.plots[plot_key].parameters.ylabel,
                },
                // ticks: {
                  // beginAtZero:true
                // },
              }],
              xAxes: [{
                afterTickToLabelConversion: function(data){
                  var xLabels = data.ticks;
                  xLabels.forEach(function (labels, i) {
                    xLabels[i] = parseFloat(xLabels[i]).toFixed(2);
                  });
                },
                scaleLabel: {
                  display: true,
                  labelString: this.result.parsed.xtriage.plots[plot_key].parameters.xlabel,
                },
                // ticks: {
                //   autoSkipPadding:4
                // },
              }],
            },
          },
        };
        break;

      case 'Measurability of Anomalous signal':
        this.data.xs = this.result.parsed.xtriage.plots[plot_key].x_data;
        this.data.ys = this.result.parsed.xtriage.plots[plot_key].y_data;
        this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString = this.result.parsed.xtriage.plots[plot_key].parameters.ylabel;
        this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = this.result.parsed.xtriage.plots[plot_key].parameters.xlabel;
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = function(data){
          var xLabels = data.ticks;
          xLabels.forEach(function (labels, i) {
            xLabels[i] = parseFloat(xLabels[i]).toFixed(2);
          });
        };
        break;

        case 'NZ test':
          this.data.xs = this.result.parsed.xtriage.plots[plot_key].x_data;
          this.data.ys = this.result.parsed.xtriage.plots[plot_key].y_data;
          this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString = this.result.parsed.xtriage.plots[plot_key].parameters.ylabel;
          this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = this.result.parsed.xtriage.plots[plot_key].parameters.xlabel;
          this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined; //function(data){
          //   var xLabels = data.ticks;
          //   xLabels.forEach(function (labels, i) {
          //     xLabels[i] = parseFloat(xLabels[i]).toFixed(2);
          //   });
          // };
          break;

        case 'L test, acentric data':
          this.data.xs = this.result.parsed.xtriage.plots[plot_key].x_data;
          this.data.ys = this.result.parsed.xtriage.plots[plot_key].y_data;
          this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString = this.result.parsed.xtriage.plots[plot_key].parameters.ylabel;
          this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = this.result.parsed.xtriage.plots[plot_key].parameters.xlabel;
          this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined; //function(data){
          //   var xLabels = data.ticks;
          //   xLabels.forEach(function (labels, i) {
          //     xLabels[i] = parseFloat(xLabels[i]).toFixed(2);
          //   });
          // };
          break;

      // case 'Anomalous & Imean CCs vs Resolution':
      //   this.data.xs = this.full_result.results.plots['Anomalous & Imean CCs vs Resolution'].x_data;
      //   this.data.ys = this.full_result.results.plots['Anomalous & Imean CCs vs Resolution'].y_data;
      //   this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString = this.full_result.results.plots['Anomalous & Imean CCs vs Resolution'].parameters.ylabel;
      //   this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = this.full_result.results.plots['Anomalous & Imean CCs vs Resolution'].parameters.xlabel;
      //   // Y-axis does not begin at 0
      //   // this.data.lineChartOptions.scales.yAxes[0].ticks.beginAtZero = false;
      //   // this.data.lineChartOptions.scaleBeginAtZero = false;
      //   // this.data.lineChartOptions.scaleStartValue = -1;
      //   this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined;
      //   break;
      //
      // case 'RMS correlation ratio':
      //   this.data.xs = this.full_result.results.plots['RMS correlation ratio'].x_data;
      //   this.data.ys = this.full_result.results.plots['RMS correlation ratio'].y_data;
      //   this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString = this.full_result.results.plots['RMS correlation ratio'].parameters.ylabel;
      //   this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = this.full_result.results.plots['RMS correlation ratio'].parameters.xlabel;
      //   this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined;
      //   break;
      //
      // case "I/sigma, Mean Mn(I)/sd(Mn(I))":
      //   this.data.xs = this.full_result.results.plots['I/sigma, Mean Mn(I)/sd(Mn(I))'].x_data;
      //   this.data.ys = this.full_result.results.plots['I/sigma, Mean Mn(I)/sd(Mn(I))'].y_data;
      //   this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString = this.full_result.results.plots['I/sigma, Mean Mn(I)/sd(Mn(I))'].parameters.ylabel;
      //   this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = this.full_result.results.plots['I/sigma, Mean Mn(I)/sd(Mn(I))'].parameters.xlabel;
      //   // Make the x labels in 1/A
      //   this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = function(data){
      //         var xLabels = data.ticks;
      //         xLabels.forEach(function (labels, i) {
      //           xLabels[i] = '1/'+(1.0/xLabels[i]).toFixed(2).toString();
      //         });
      //   };
      //   break;
      //
      // case "rs_vs_res":
      //   this.data.xs = this.full_result.results.plots['rs_vs_res'].x_data;
      //   this.data.ys = this.full_result.results.plots['rs_vs_res'].y_data;
      //   this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString = this.full_result.results.plots['rs_vs_res'].parameters.ylabel;
      //   this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = this.full_result.results.plots['rs_vs_res'].parameters.xlabel;
      //   // Make the x labels in A
      //   this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = function(data){
      //         var xLabels = data.ticks;
      //         xLabels.forEach(function (labels, i) {
      //           xLabels[i] = (1.0/xLabels[i]).toFixed(2);
      //         });
      //   };
      //   break;
      //
      // case "Average I, RMS deviation, and Sd":
      //   this.data.xs = this.full_result.results.plots['Average I, RMS deviation, and Sd'].x_data;
      //   this.data.ys = this.full_result.results.plots['Average I, RMS deviation, and Sd'].y_data;
      //   this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString = this.full_result.results.plots['Average I, RMS deviation, and Sd'].parameters.ylabel;
      //   this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = this.full_result.results.plots['Average I, RMS deviation, and Sd'].parameters.xlabel;
      //   this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined;
      //   break;
      //
      // case 'Completeness':
      //   this.data.xs = this.full_result.results.plots['Completeness'].x_data;
      //   this.data.ys = this.full_result.results.plots['Completeness'].y_data;
      //   this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString = this.full_result.results.plots['Completeness'].parameters.ylabel;
      //   this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = this.full_result.results.plots['Completeness'].parameters.xlabel;
      //   this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined;
      //   break;
      //
      // case 'Redundancy':
      //   this.data.xs = this.full_result.results.plots['Redundancy'].x_data;
      //   this.data.ys = this.full_result.results.plots['Redundancy'].y_data;
      //   this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString = this.full_result.results.plots['Redundancy'].parameters.ylabel;
      //   this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = this.full_result.results.plots['Redundancy'].parameters.xlabel;
      //   this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined;
      //   break;
      //
      // case 'Radiation Damage':
      //   this.data.xs = this.full_result.results.plots['Radiation Damage'].x_data;
      //   this.data.ys = this.full_result.results.plots['Radiation Damage'].y_data;
      //   this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString = this.full_result.results.plots['Radiation Damage'].parameters.ylabel;
      //   this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = this.full_result.results.plots['Radiation Damage'].parameters.xlabel;
      //   this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined;
      //   break;

      default:
        this.data = false;
    }

  }

}
