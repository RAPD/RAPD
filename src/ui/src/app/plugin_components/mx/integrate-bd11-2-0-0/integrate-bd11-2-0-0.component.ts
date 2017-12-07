import { Component,
         ComponentFactory,
         ComponentFactoryResolver,
         Input,
         OnDestroy,
         OnInit,
         ViewChild,
         ViewContainerRef } from '@angular/core';

import { MatDialog,
         MAT_DIALOG_DATA,
         MatSnackBar,
         MatToolbarModule } from '@angular/material';

import { ReplaySubject }   from 'rxjs/Rx';

import { RestService } from '../../../shared/services/rest.service';
import { WebsocketService } from '../../../shared/services/websocket.service';
import { GlobalsService } from '../../../shared/services/globals.service';

import { RunDialogComponent } from '../run-dialog/run-dialog.component';
import { ReintegrateDialogComponent } from '../reintegrate-dialog/reintegrate-dialog.component';
import { DialogSelectProjectComponent } from '../../../shared/components/dialog-select-project/dialog-select-project.component';

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
export class IntegrateBd11200Component implements OnInit, OnDestroy {

  @Input()
  current_result: any;

  incomingData$: ReplaySubject<string>;

  full_result: any = {process:{status:0}, results:{}};

  view_mode: string = 'summary';

  selected_plot: string;
  selected_plot_label:string;
  plot_select_labels:any = {
    'Rmerge vs Frame': 'Rmerge vs Batch',
    'I/sigma, Mean Mn(I)/sd(Mn(I))': 'I / sigma I',
    'Average I, RMS deviation, and Sd': 'I vs Resolution',
    'Imean/RMS scatter': 'I / RMS',
    'rs_vs_res': 'R Factors',
    'Redundancy': 'Redundancy',
    'Completeness': 'Completeness',
    'Radiation Damage': 'Radiation Damage',
  };

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
      }
    }
  };

  // @ViewChild(BaseChartDirective) private _chart;
  @ViewChild('analysistarget', { read: ViewContainerRef }) analysistarget;

  analysis_component: any;

  objectKeys = Object.keys;

  constructor(private componentfactoryResolver: ComponentFactoryResolver,
              private rest_service: RestService,
              private websocket_service: WebsocketService,
              private globals_service: GlobalsService,
              public dialog: MatDialog,
              public snackBar: MatSnackBar) { }

  ngOnInit() {
    // Subscribe to results for the displayed result
    this.incomingData$ = this.websocket_service.subscribeResultDetails(
      this.current_result.data_type,
      this.current_result.plugin_type,
      this.current_result.result_id,
      this.current_result._id);
    this.incomingData$.subscribe(x => this.handleIncomingData(x));
  }

  ngOnDestroy() {
    this.websocket_service.unsubscribeResultDetails(this.incomingData$);
  }

  public handleIncomingData(data: any) {
    console.log('handleIncomingData', data);
    this.full_result = data;

    // Select the default plot to show
    if (data.results) {
      if (data.results.plots) {
        if ('Rmerge vs Frame' in data.results.plots) {
          this.selected_plot = 'Rmerge vs Frame';
          this.setPlot('Rmerge vs Frame');
        }
      }
    }
  }

  // Display the header information
  displayRunInfo() {



    let config = {
      data: {
        run_id:this.full_result.process.run_id,
        image_id:this.full_result.process.image_id
      }
    };

    let dialogRef = this.dialog.open(RunDialogComponent, config);
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

  onPlotSelect(plot_key:string) {

    console.log('onPlotSelect', plot_key);
    this.setPlot(plot_key);

  }

  // Set up the plot
  setPlot(plot_key:string) {

    console.log('setPlot', plot_key);

    let plot_result = this.full_result.results.plots[plot_key];

    // Consistent features
    this.data.xs = plot_result.x_data;
    this.data.ys = plot_result.y_data;
    this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString = plot_result.parameters.ylabel;
    this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = plot_result.parameters.xlabel;

    switch (plot_key) {

      case 'Rmerge vs Frame':
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined;
        // Axis options
        // this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = function(data){
        //   var xLabels = data.ticks;
        //   xLabels.forEach(function (labels, i) {
        //       if (i % 10 !== 0){
        //           xLabels[i] = '';
        //       }
        //   });
        //   // xLabels.push('360');
        // };
        break;

      case 'Imean/RMS scatter':
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined;
        break;

      case 'Anomalous & Imean CCs vs Resolution':
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined;
        break;

      case 'RMS correlation ratio':
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined;
        break;

      case "I/sigma, Mean Mn(I)/sd(Mn(I))":
        // Make the x labels in 1/A
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = function(data){
              var xLabels = data.ticks;
              xLabels.forEach(function (labels, i) {
                xLabels[i] = '1/'+(1.0/xLabels[i]).toFixed(2).toString();
              });
        };
        break;

      case "rs_vs_res":
        // Make the x labels in A
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = function(data){
              var xLabels = data.ticks;
              xLabels.forEach(function (labels, i) {
                xLabels[i] = (1.0/xLabels[i]).toFixed(2);
              });
        };
        // X-axis label
        this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = 'Dmid (\u00C5)';
        break;

      case "Average I, RMS deviation, and Sd":
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = function(data){
          var xLabels = data.ticks;
          xLabels.forEach(function (labels, i) {
            xLabels[i] = (1.0/xLabels[i]).toFixed(2);
          });
        };
        // X-axis label
        this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = 'Dmid (\u00C5)';
        // Y-axis label
        this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString = 'Intensity';
        break;

      case 'Completeness':
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = function(data){
          var xLabels = data.ticks;
          xLabels.forEach(function (labels, i) {
            xLabels[i] = (1.0/xLabels[i]).toFixed(2);
          });
        };
        // X-axis label
        this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = 'Dmid (\u00C5)';
        break;

      case 'Redundancy':
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = function(data){
          var xLabels = data.ticks;
          xLabels.forEach(function (labels, i) {
            xLabels[i] = (1.0/xLabels[i]).toFixed(2);
          });
        };
        // X-axis label
        this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = 'Dmid (\u00C5)';
        break;

      case 'Radiation Damage':
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined;
        break;

      default:
        this.data = false;
    }
    console.log(this.data);
  }

  openReintegrateDialog() {

    let config = {
      data: this.full_result };

    let dialogRef = this.dialog.open(ReintegrateDialogComponent, config);

  }

  openProjectDialog() {
    let config = {data:this.current_result};

    let dialogRef = this.dialog.open(DialogSelectProjectComponent, config);
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

  // Start the download of data
  initDownload(record:any) {

    console.log(record);

    // Signal that the request has been made
    let snackBarRef = this.snackBar.open('Download request submitted', 'Ok', {
      duration: 2000,
    });

    this.rest_service.getDownloadById(record._id, record.path)
                     .subscribe(
                       result => {},
                       error => {}
                     );
  }
}

// this.rest_service.getImageData(this.full_result.process.image_id)
//                  .subscribe(
//                    image_data => console.log(image_data),
//                    error => console.error(error));
