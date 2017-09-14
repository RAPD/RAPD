import { Component,
         ComponentFactory,
         ComponentFactoryResolver,
         Input,
         OnInit,
         ViewChild,
         ViewContainerRef } from '@angular/core';
import { MdDialog,
         MD_DIALOG_DATA } from '@angular/material';
import { ReplaySubject }   from 'rxjs/Rx';

import { WebsocketService } from '../../../shared/services/websocket.service';
import { GlobalsService } from '../../../shared/services/globals.service';

// Import analysis plugin components here
import * as mx from '../';
var analysis_values = [];
var analysis_components = {};
for (let key in mx) {
  // console.log(key);
  if (key.match('Analysis')) {
    // console.log('YES');
    analysis_values.push(mx[key]);
    analysis_components[key.toLowerCase()] = mx[key];
  }
}

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
  view_mode: string = 'summary';
  data:any = {
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
            labelString: '',
          },
          ticks: {},
        }],
        xAxes: [{
          scaleLabel: {
            display: true,
            labelString: '',
          },
          ticks: {},
        }],
      },
      tooltips: {
        callbacks: {}
      },
    },
  };

  // @ViewChild(BaseChartDirective) private _chart;
  @ViewChild('analysistarget', { read: ViewContainerRef }) analysistarget;
  analysis_component: any;

  constructor(private componentfactoryResolver: ComponentFactoryResolver,
              private websocket_service: WebsocketService,
              private globals_service: GlobalsService,
              public dialog: MdDialog) { }

  ngOnInit() {
    // Subscribe to results for the displayed result
    this.incomingData$ = this.websocket_service.subscribeResultDetails(
      this.current_result.result_type,
      this.current_result.result_id);
    this.incomingData$.subscribe(x => this.handleIncomingData(x));
  }

  public handleIncomingData(data: any) {
    console.log('handleIncomingData', data);
    this.full_result = data;

    // Select the default plot to show
    if ('Rmerge vs Frame' in data.results.plots) {
      this.selected_plot = 'Rmerge vs Frame';
      this.setPlot('Rmerge vs Frame');
    }
  }

  onPlotSelect(plot_key:string) {

    console.log('onPlotSelect', plot_key);
    this.setPlot(plot_key);

  }

  // Set up the plot
  setPlot(plot_key:string) {

    console.log('setPlot', plot_key);

    let plot_data = this.full_result.results.plots[plot_key];

    this.data.xs = plot_data.x_data;
    this.data.ys = plot_data.y_data;

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
                // ticks: {
                  // beginAtZero:true
                // },
              }],
              xAxes: [{
                afterTickToLabelConversion: undefined,
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
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined;
        break;

      case 'Anomalous & Imean CCs vs Resolution':
        this.data.xs = this.full_result.results.plots['Anomalous & Imean CCs vs Resolution'].x_data;
        this.data.ys = this.full_result.results.plots['Anomalous & Imean CCs vs Resolution'].y_data;
        this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString = this.full_result.results.plots['Anomalous & Imean CCs vs Resolution'].parameters.ylabel;
        this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = this.full_result.results.plots['Anomalous & Imean CCs vs Resolution'].parameters.xlabel;
        // Y-axis does not begin at 0
        // this.data.lineChartOptions.scales.yAxes[0].ticks.beginAtZero = false;
        // this.data.lineChartOptions.scaleBeginAtZero = false;
        // this.data.lineChartOptions.scaleStartValue = -1;
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined;
        break;

      case 'RMS correlation ratio':
        this.data.xs = this.full_result.results.plots['RMS correlation ratio'].x_data;
        this.data.ys = this.full_result.results.plots['RMS correlation ratio'].y_data;
        this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString = this.full_result.results.plots['RMS correlation ratio'].parameters.ylabel;
        this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = this.full_result.results.plots['RMS correlation ratio'].parameters.xlabel;
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined;
        break;

      case "I/sigma, Mean Mn(I)/sd(Mn(I))":
        this.data.xs = this.full_result.results.plots['I/sigma, Mean Mn(I)/sd(Mn(I))'].x_data;
        this.data.ys = this.full_result.results.plots['I/sigma, Mean Mn(I)/sd(Mn(I))'].y_data;
        this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString = this.full_result.results.plots['I/sigma, Mean Mn(I)/sd(Mn(I))'].parameters.ylabel;
        this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = this.full_result.results.plots['I/sigma, Mean Mn(I)/sd(Mn(I))'].parameters.xlabel;
        // Make the x labels in 1/A
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = function(data){
              var xLabels = data.ticks;
              xLabels.forEach(function (labels, i) {
                xLabels[i] = '1/'+(1.0/xLabels[i]).toFixed(2).toString();
              });
        };
        break;

      case "rs_vs_res":
        this.data.xs = this.full_result.results.plots['rs_vs_res'].x_data;
        this.data.ys = this.full_result.results.plots['rs_vs_res'].y_data;
        this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString = this.full_result.results.plots['rs_vs_res'].parameters.ylabel;
        this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = this.full_result.results.plots['rs_vs_res'].parameters.xlabel;
        // Make the x labels in A
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = function(data){
              var xLabels = data.ticks;
              xLabels.forEach(function (labels, i) {
                xLabels[i] = (1.0/xLabels[i]).toFixed(2);
              });
        };
        break;

      case "Average I, RMS deviation, and Sd":
        this.data.xs = this.full_result.results.plots['Average I, RMS deviation, and Sd'].x_data;
        this.data.ys = this.full_result.results.plots['Average I, RMS deviation, and Sd'].y_data;
        this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString = this.full_result.results.plots['Average I, RMS deviation, and Sd'].parameters.ylabel;
        this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = this.full_result.results.plots['Average I, RMS deviation, and Sd'].parameters.xlabel;
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined;
        break;

      case 'Completeness':
        this.data.xs = this.full_result.results.plots['Completeness'].x_data;
        this.data.ys = this.full_result.results.plots['Completeness'].y_data;
        this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString = this.full_result.results.plots['Completeness'].parameters.ylabel;
        this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = this.full_result.results.plots['Completeness'].parameters.xlabel;
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined;
        break;

      case 'Redundancy':
        this.data.xs = this.full_result.results.plots['Redundancy'].x_data;
        this.data.ys = this.full_result.results.plots['Redundancy'].y_data;
        this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString = this.full_result.results.plots['Redundancy'].parameters.ylabel;
        this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = this.full_result.results.plots['Redundancy'].parameters.xlabel;
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined;
        break;

      case 'Radiation Damage':
        this.data.xs = this.full_result.results.plots['Radiation Damage'].x_data;
        this.data.ys = this.full_result.results.plots['Radiation Damage'].y_data;
        this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString = this.full_result.results.plots['Radiation Damage'].parameters.ylabel;
        this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = this.full_result.results.plots['Radiation Damage'].parameters.xlabel;
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined;
        break;

      default:
        this.data = false;
    }
    // console.log(this.data);
  }

  onViewModeSelect(view_mode:string) {

    var self = this;

    console.log(view_mode);

    setTimeout(function() {
      if (view_mode === 'analysis') {
        // If there is analysis data, determine the component to use
        if (self.full_result.results.analysis) {

          let plugin = self.full_result.results.analysis.plugin;
          const component_name = (plugin.type + plugin.id + plugin.version.replace(/\./g, '') + 'component').toLowerCase();
          console.log(component_name);
          console.log(analysis_components);

          // Create a componentfactoryResolver instance
          const factory = self.componentfactoryResolver.resolveComponentFactory(analysis_components[component_name]);

          // Create the component
          self.analysis_component = self.analysistarget.createComponent(factory);
          console.log(self.analysistarget);
          // Set the component current_result value
          // component.instance.current_result = event.value;
          self.analysis_component.instance.result = self.full_result.results.analysis;
        }
      }
    }, 100);
  }

  // Change the current result's display to 'pinned'
  pinResult(result) {
    result.display = 'pinned';
    this.websocket_service.updateResult(result);
  }

  // Change the current result's display to undefined
  undefResult(result) {
    result.display = '';
    this.websocket_service.updateResult(result);
  }

  // change the current result's display status to 'junked'
  junkResult(result) {
    result.display = 'junked';
    this.websocket_service.updateResult(result);
  }

}
