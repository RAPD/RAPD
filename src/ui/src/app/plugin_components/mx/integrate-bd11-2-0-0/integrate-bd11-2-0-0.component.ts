import { Component,
         ComponentFactory,
         ComponentFactoryResolver,
         Input,
         OnChanges,
         OnInit,
         SimpleChanges,
         ViewChild,
         ViewContainerRef,
         trigger,
         transition,
         style,
         animate } from '@angular/core';
import { MdDialog,
         MD_DIALOG_DATA } from '@angular/material';
import { ReplaySubject }   from 'rxjs/Rx';
// import { BaseChartDirective } from 'ng2-charts';
import { ResultsService } from '../../../shared/services/results.service';
// import { AnalysisF068200Component } from '../analysis-f068-2-0-0/analysis-f068-2-0-0.component';

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
export class IntegrateBd11200Component implements OnInit, OnChanges {

  objectKeys = Object.keys;
  @Input() current_result: any;
  incomingData$: ReplaySubject<string>;

  full_result: any;
  selected_plot: string;
  view_mode: string = 'summary';
  data: any;

  // Variables for coordinating the collapsible cards
  log_xds_idxref_collapsed: boolean = true;
  log_xds_integrate_collapsed: boolean = true;
  log_xds_correct_collapsed: boolean = true;
  log_aimless_collapsed: boolean = true;
  log_pointless_collapsed: boolean = true;

  // @ViewChild(BaseChartDirective) private _chart;
  @ViewChild('analysistarget', { read: ViewContainerRef }) analysistarget;
  analysis_component: any;

  constructor(private componentfactoryResolver: ComponentFactoryResolver,
              private results_service: ResultsService,
              public dialog: MdDialog) { }

  ngOnInit() {
    // Subscribe to results for the displayed result
    this.incomingData$ = this.results_service.subscribeResultDetails(
      this.current_result.result_type,
      this.current_result.result_id);
    this.incomingData$.subscribe(x => this.handleIncomingData(x));
  }

  ngOnChanges(changes: SimpleChanges) {
    console.log(changes);
  }

  // lineChart
  // public lineChartOptions:any = {
  //   responsive: true,
  //   legend: {
  //     display: true,
  //     position: 'right',
  //   }
  // };
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
  // public lineChartLegend:boolean = true;
  // public lineChartType:string = 'line';

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

}
