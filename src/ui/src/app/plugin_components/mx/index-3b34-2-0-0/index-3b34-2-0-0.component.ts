import { Component,
         Input,
         OnDestroy,
         OnInit } from "@angular/core";

import { MatDialog, MAT_DIALOG_DATA } from "@angular/material/dialog";
// import { MatToolbarModule } from "@angular/material/toolbar";

import { ReplaySubject } from "rxjs/Rx";

import { WebsocketService } from "../../../shared/services/websocket.service";
import { RestService } from "../../../shared/services/rest.service";
import { GlobalsService } from "../../../shared/services/globals.service";

import { HeaderDialogComponent } from "../header-dialog/header-dialog.component";
import { ReindexDialogComponent } from "./reindex-dialog/reindex-dialog.component";
import { DialogSelectProjectComponent } from "../../../shared/components/dialog-select-project/dialog-select-project.component";

@Component({
  selector: "app-index-3b34-2-0-0",
  templateUrl: "./index-3b34-2-0-0.component.html",
  styleUrls: ["./index-3b34-2-0-0.component.css"],
})
export class Index3b34200Component implements OnDestroy {

  // @Input() currentResult: any;

  @Input() set incomingResult(currentResult: any) {
    this.setCurrentResult(currentResult);
  }
  public currentResult:any;

  private incomingData$: ReplaySubject<string>;

  public fullResult:any = { process: { status: 0 }, results: {} };

  viewMode: string = "summary";

  public selectedPlot:string = "osc_range";
  public selectedPlotLabel:string = "";
  plotSelectLabels: any = {
    // 'background':'Background',
    // 'exposure':'Exposure',
    osc_range: "Osc Range NORM",
    osc_range_anom: "Osc Range ANOM",
    max_delta_omega: "Max Oscillation",
    rad_damage: "Radiation Damage",
    wilson: "Wilson",
  };

  data: any = {
    lineChartType: "line",
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
        position: "right",
        labels: {
          boxWidth: 3,
        },
      },
      responsive: true,
      scales: {
        yAxes: [
          {
            scaleLabel: {
              display: true,
              labelString: "",
            },
            ticks: {},
          },
        ],
        xAxes: [
          {
            scaleLabel: {
              display: true,
              labelString: "",
            },
            ticks: {},
          },
        ],
      },
      tooltips: {
        callbacks: {},
      },
    },
  };

  objectKeys = Object.keys;
  // objectToArray(input:any): [any] {
  //   return [].concat.apply(
  //     [],
  //     Object.keys(input).map((key, index) => {
  //       return input[key];
  //     })
  //   );
  // }


  constructor(
    private websocketService: WebsocketService,
    private restService: RestService,
    public globalsService: GlobalsService,
    public dialog: MatDialog
  ) {}

  // ngOnInit() {}

  ngOnDestroy() {
    this.websocketService.unsubscribeResultDetails(this.incomingData$);
  }

  private setCurrentResult(data:any):void {

    // console.log('setCurrentResult');

    // Unsubscribe to changes of previously displayed result
    if (this.currentResult !== undefined) {
      this.currentResult = undefined;
      this.fullResult = { process: { status: 0 }, results: {} };
      this.websocketService.unsubscribeResultDetails(this.incomingData$);
      this.incomingData$.unsubscribe();
    }

    // Save data
    this.currentResult = data;

    // Connect to websocket results for this result
    this.incomingData$ = this.websocketService.subscribeResultDetails(
      this.currentResult.data_type,
      this.currentResult.plugin_type,
      this.currentResult.result_id,
      this.currentResult._id
    );
    this.incomingData$.subscribe(x => this.handleIncomingData(x));
  }

  public handleIncomingData(data: any) {

    // console.log("handleIncomingData", data);

    // Set full_result to incoming data
    this.fullResult = data;

    // Load default plot
    if ("results" in this.fullResult) {
      if ("plots" in this.fullResult.results) {
        if ("osc_range" in this.fullResult.results.plots) {
          this.selectedPlot = "osc_range";
          this.setPlot("osc_range");
        }
      }
    }
  }

  // Display the header information
  displayHeader(imageData:any) {
    const config = {
      data: {
        image_data: imageData,
        image_id: false,
      },
    };
    const dialogRef = this.dialog.open(HeaderDialogComponent, config);
  }

  // Set up the plot
  setPlot(plotKey:string) {
    // console.log('setPlot', plotKey, this.selectedPlot);

    // Load the result for convenience
    const plotResult = this.fullResult.results.plots[plotKey];
    // console.log(plotResult);

    // Set the label in the UI
    this.selectedPlotLabel = plotResult.parameters.toplabel;

    // Certain features are consistent
    this.data.xs = plotResult.x_data;
    this.data.ys = plotResult.y_data;
    this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString = plotResult.parameters.ylabel;
    this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString =  plotResult.parameters.xlabel;

    switch (plotKey) {
      // case 'background':
      //   this.data.xs = plotResult.x_data;
      //   this.data.ys = plotResult.y_data;
      //   // this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined;
      //   break;
      //
      // case 'exposure':
      //   this.data.ys = plotResult.y_data;
      //   this.data.xs = plotResult.x_data;
      //   // this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString = plotResult.parameters.ylabel;
      //   // this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = plotResult.parameters.xlabel;
      //   // this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined;
      //   break;

      case "osc_range":
      case "osc_range_anom":
        // First 5 plots, and no points
        this.data.ys = plotResult.y_data.slice(0, 5).map((el:any) => {
          const o = Object.assign({}, el);
          o.pointRadius = 0;
          return o;
        });
        // axis options
        // this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString = 'Required Sweep Width';
        this.data.lineChartOptions.scales.yAxes[0].ticks.beginAtZero = true;
        // this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = 'Starting Omega';
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = (data:any) => {
          const xLabels = data.ticks;
          xLabels.forEach((labels:any, i:number) => {
            if (i % 10 !== 0) {
              xLabels[i] = "";
            }
          });
          xLabels.push("360");
        };
        this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString =
          plotResult.parameters.xlabel + " (\u00B0)";
        this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString =
          plotResult.parameters.ylabel + " (\u00B0)";
        // Tooltips
        this.data.lineChartOptions.tooltips.callbacks.title = (tooltipItem:any, data:any) => {
          return data.labels[tooltipItem[0].index] + "° start";
        };
        this.data.lineChartOptions.tooltips.callbacks.label = (tooltipItem:any, data:any) => {
          return tooltipItem.yLabel + "° width";
        };
        break;

      case "max_delta_omega":
        // Limit to 1st 5 plots and take out the dots
        this.data.ys = plotResult.y_data.slice(0, 5).map((el:any) => {
          const o = Object.assign({}, el);
          o.pointRadius = 0;
          return o;
        });
        this.data.xs = plotResult.x_data;
        // Axis options
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = (data:any) => {
          const xLabels = data.ticks;
          xLabels.forEach((labels:any, i:number) => {
            if (i % 10 !== 0) {
              xLabels[i] = "";
            }
          });
          xLabels.push("180");
        };
        this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString =
          plotResult.parameters.xlabel + " (\u00B0)";
        this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString =
          plotResult.parameters.ylabel + " (\u00B0)";
        // Tooltips
        this.data.lineChartOptions.tooltips.callbacks.title = (tooltipItem:any, data:any) => {
          return data.labels[tooltipItem[0].index] + "°";
        };
        this.data.lineChartOptions.tooltips.callbacks.label = (tooltipItem:any, data:any) => {
          return tooltipItem.yLabel + "° width";
        };
        break;

      case "rad_damage":
        // Axis options
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = (data:any) => {
          const xLabels = data.ticks;
          xLabels.forEach((labels:any, i:number) => {
            if (i % 10 !== 0) {
              xLabels[i] = "";
            }
          });
          xLabels.push("180");
        };
        this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString =
          plotResult.parameters.xlabel + " (\u00B0)";
        // Tooltips
        this.data.lineChartOptions.tooltips.callbacks.title = (tooltipItem:any, data:any) => {
          return data.labels[tooltipItem[0].index] + "\u00B0";
        };
        this.data.lineChartOptions.tooltips.callbacks.label = (tooltipItem:any, data:any) => {
          return tooltipItem.yLabel;
        };
        break;

      case "wilson":
        // Take out the dots
        this.data.ys = plotResult.y_data.map((el:any) => {
          const o = Object.assign({}, el);
          o.pointRadius = 0;
          return o;
        });
        // Axis options
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = (data:any) => {
          const xLabels = data.ticks;
          xLabels.forEach((labels:any, i:number) => {
            xLabels[i] = Math.sqrt(1 / parseFloat(xLabels[i])).toFixed(2);
          });
        };
        this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString =
          plotResult.parameters.xlabel + " (\u00C5)";
        // Tooltips
        this.data.lineChartOptions.tooltips.callbacks.title = (tooltipItem:any, data:any) => {
          return (
            Math.sqrt(
              1 / parseFloat(data.labels[tooltipItem[0].index])
            ).toFixed(2) + "\u00C5"
          );
        };
        this.data.lineChartOptions.tooltips.callbacks.label = (tooltipItem:any, data:any) => {
          return tooltipItem.yLabel;
        };
        break;

      default:
        break;
    }

    // console.log(this.data);
  }

  openReindexDialog() {
    const config = {
      // height: '600px',
      // width: '500px',
      data: this.fullResult,
    };

    const dialogRef = this.dialog.open(ReindexDialogComponent, config);
  }

  // Open the add to project dialog
  openProjectDialog() {
    const config = { data: this.currentResult };
    const dialogRef = this.dialog.open(DialogSelectProjectComponent, config);
  }

  // Change the current result's display to 'pinned'
  pinResult(result:any) {
    result.display = "pinned";
    this.websocketService.updateResult(result);
  }

  // Change the current result's display to undefined
  undefResult(result:any) {
    result.display = "";
    this.websocketService.updateResult(result);
  }

  // change the current result's display status to 'junked'
  junkResult(result:any) {
    result.display = "junked";
    this.websocketService.updateResult(result);
  }

  // TODO
  printPage() {
    // var doc = jsPDF();
    //
    // doc.text(20, 20, 'Hello world!');
    // doc.text(20, 30, 'This is client-side Javascript, pumping out a PDF.');
    // doc.save('Test.pdf');
  }

  round_ten(value: number): number {
    return Math.round(value / 10) * 10;
  }
}
