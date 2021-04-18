import {
  Component,
  // ComponentFactory,
  ComponentFactoryResolver,
  Input,
  OnDestroy,
  OnInit,
  ViewChild,
  ViewContainerRef
} from "@angular/core";

import { MatDialog, MAT_DIALOG_DATA } from "@angular/material/dialog";
import { MatSnackBar } from "@angular/material/snack-bar";
// import { MatToolbarModule } from "@angular/material/toolbar";

import { ReplaySubject } from "rxjs/Rx";

import { GlobalsService } from "../../../shared/services/globals.service";
import { RestService } from "../../../shared/services/rest.service";
import { WebsocketService } from "../../../shared/services/websocket.service";

import { DialogSelectProjectComponent } from "../../../shared/components/dialog-select-project/dialog-select-project.component";
import { MrDialogComponent } from "../mr-dialog/mr-dialog.component";
import { ReintegrateDialogComponent } from "../reintegrate-dialog/reintegrate-dialog.component";
import { RunDialogComponent } from "../run-dialog/run-dialog.component";
import { SadDialogComponent } from "../sad-dialog/sad-dialog.component";


// Import encapsulated plugin components here
import * as mx from "../";
const ANALYSIS_COMPONENTS: any = {};
const PDBQUERY_COMPONENTS: any = {};
// tslint:disable-next-line: forin
for (const KEY in mx) {
  // Analysis
  if (KEY.match("Analysis")) {
    ANALYSIS_COMPONENTS[KEY.toLowerCase()] = mx[KEY];
  }
  // PDBQuery
  if (KEY.match("Pdbquery")) {
    PDBQUERY_COMPONENTS[KEY.toLowerCase()] = mx[KEY];
  }
}

@Component({
  selector: "app-integrate-bd11-2-0-0",
  templateUrl: "./integrate-bd11-2-0-0.component.html",
  styleUrls: ["./integrate-bd11-2-0-0.component.css"],
})
export class IntegrateBd11200Component implements OnDestroy {

  @Input() set incomingResult(currentResult: any) {
    this.setCurrentResult(currentResult);
  }
  public currentResult: any = undefined;

  private incomingData$: ReplaySubject<string>;

  public fullResult: any = { process: { status: 0 }, results: {} };

  naive: boolean = true;

  public viewMode: string = "summary";

  public selectedPlot: string = "Rmerge vs Frame";
  public selectedPlotLabel: string = "";
  public plotSelectLabels: any = {
    "Rmerge vs Frame": "Rmerge vs Batch",
    "I/sigma, Mean Mn(I)/sd(Mn(I))": "I / sigma I",
    "Average I, RMS deviation, and Sd": "I vs Resolution",
    "Imean/RMS scatter": "I / RMS",
    rs_vs_res: "R Factors",
    Redundancy: "Redundancy",
    Completeness: "Completeness",
    "Radiation Damage": "Radiation Damage",
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

  // @ViewChild(BaseChartDirective) private _chart;
  @ViewChild("analysistarget", { read: ViewContainerRef }) public analysisTarget: any;
  @ViewChild("pdbquerytarget", { read: ViewContainerRef }) public pdbqueryTarget: any;

  public analysisComponent: any;
  public pdbqueryComponent: any;

  public objectKeys = Object.keys;


  constructor(
    private componentfactoryResolver: ComponentFactoryResolver,
    private restService: RestService,
    private websocketService: WebsocketService,
    public globalsService: GlobalsService,
    public dialog: MatDialog,
    public snackBar: MatSnackBar
  ) {}

  // public ngOnInit() {}

  public ngOnDestroy() {
    this.websocketService.unsubscribeResultDetails(this.incomingData$);
  }

  private setCurrentResult(data: any):void {

    // console.log('setCurrentResult');

    // Unsubscribe to changes of previously displayed result
    if (this.currentResult !== undefined) {
      this.currentResult = undefined;
      this.fullResult = { process: { status: 0 }, results: {} };
      this.naive = true;
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

    console.log("handleIncomingData", data);

    this.fullResult = data;

    // Select the default plot to show
    if (this.naive && data.results) {
      // Plots
      if (data.results.plots) {
        if ("Rmerge vs Frame" in data.results.plots) {
          this.selectedPlot = "Rmerge vs Frame";
          this.setPlot("Rmerge vs Frame");
        }
      }
      this.naive = false;
    }
  }

  // Display the header information
  public displayRunInfo() {
    const config = {
      data: {
        run_id: this.fullResult.process.run_id,
        image_id: this.fullResult.process.image_id,
      },
    };

    const dialogRef = this.dialog.open(RunDialogComponent, config);
  }

  public onViewModeSelect(event: any) {
    // console.log('onViewModeSelect', event.value);

    const self = this;

    // Wait 100ms and then load up the interface
    setTimeout(() => {
      // Looking at an analysis
      if (event.value === "analysis") {
        // console.log(self.full_result.results.analysis);

        // If there is analysis data, determine the component to use
        if (self.fullResult.results.analysis) {
          const plugin = self.fullResult.results.analysis.plugin;
          const componentName = (
            plugin.type +
            plugin.id +
            plugin.version.replace(/\./g, "") +
            "component"
          ).toLowerCase();

          // Create a componentfactoryResolver instance
          const factory = self.componentfactoryResolver.resolveComponentFactory(
            ANALYSIS_COMPONENTS[componentName]
          );

          // Create the component
          self.analysisComponent = self.analysisTarget.createComponent(
            factory
          );

          // Set the component currentResult value
          self.analysisComponent.instance.result =
            self.fullResult.results.analysis;
        }

        // PDBQuery
      } else if (event.value === "pdbquery") {
        // If there is analysis data, determine the component to use
        if (self.fullResult.results.pdbquery) {
          const plugin = self.fullResult.results.pdbquery.plugin;

          const componentName = (
            plugin.type +
            plugin.id +
            plugin.version.replace(/\./g, "") +
            "component"
          ).toLowerCase();

          // Create a componentfactoryResolver instance
          const factory = self.componentfactoryResolver.resolveComponentFactory(
            PDBQUERY_COMPONENTS[componentName]
          );

          // Create the component
          self.pdbqueryComponent = self.pdbqueryTarget.createComponent(
            factory
          );

          // Set the component currentResult value
          self.pdbqueryComponent.instance.result =
            self.fullResult.results.pdbquery;
        }
      }
    }, 200);
  }

  // Set up the plot
  public setPlot(plotKey: string) {
    // console.log("setPlot", plot_key);

    const plotResult = this.fullResult.results.plots[plotKey];

    // Consistent features
    this.data.xs = plotResult.x_data;
    this.data.ys = plotResult.y_data;
    this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString =
      plotResult.parameters.ylabel;
    this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString =
      plotResult.parameters.xlabel;

    switch (plotKey) {
      case "Rmerge vs Frame":
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined;
        break;

      case "Imean/RMS scatter":
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined;
        break;

      case "Anomalous & Imean CCs vs Resolution":
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined;
        break;

      case "RMS correlation ratio":
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined;
        break;

      case "I/sigma, Mean Mn(I)/sd(Mn(I))":
        // Make the x labels in 1/A
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = (data: any) => {
          const xLabels = data.ticks;
          xLabels.forEach((labels: any, i: number) => {
            xLabels[i] = "1/" + (1.0 / xLabels[i]).toFixed(2).toString();
          });
        };
        break;

      case "rs_vs_res":
        // Make the x labels in A
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = (data: any) => {
          const xLabels = data.ticks;
          xLabels.forEach((labels: any, i: number) => {
            xLabels[i] = (1.0 / xLabels[i]).toFixed(2);
          });
        };
        // X-axis label
        this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = "Dmid (\u00C5)";
        break;

      case "Average I, RMS deviation, and Sd":
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = (data: any) => {
          const xLabels = data.ticks;
          xLabels.forEach((labels: any, i: number) => {
            xLabels[i] = (1.0 / xLabels[i]).toFixed(2);
          });
        };
        // X-axis label
        this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = "Dmid (\u00C5)";
        // Y-axis label
        this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString = "Intensity";
        break;

      case "Completeness":
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = (data: any) => {
          const xLabels = data.ticks;
          xLabels.forEach((labels: any, i: number) => {
            xLabels[i] = (1.0 / xLabels[i]).toFixed(2);
          });
        };
        // X-axis label
        this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = "Dmid (\u00C5)";
        break;

      case "Redundancy":
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = (data: any) => {
          const xLabels = data.ticks;
          xLabels.forEach((labels: any, i: number) => {
            xLabels[i] = (1.0 / xLabels[i]).toFixed(2);
          });
        };
        // X-axis label
        this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = "Dmid (\u00C5)";
        break;

      case "Radiation Damage":
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined;
        break;

      default:
        this.data = false;
    }
  }

  public openReintegrateDialog() {
    const config = {
      data: this.fullResult,
    };

    const dialogRef = this.dialog.open(ReintegrateDialogComponent, config);
  }

  public openMrDialog() {
    const config = {
      data: this.fullResult,
    };

    const dialogRef = this.dialog.open(MrDialogComponent, config);
  }

  public openSadDialog() {
    const config = {
      data: this.fullResult,
    };

    const dialogRef = this.dialog.open(SadDialogComponent, config);
  }

  public openProjectDialog() {
    const config = { data: this.currentResult };

    const dialogRef = this.dialog.open(DialogSelectProjectComponent, config);
  }

  // Change the current result's display to 'pinned'
  public pinResult(result: any) {
    result.display = "pinned";
    this.websocketService.updateResult(result);
  }

  // Change the current result's display to undefined
  public undefResult(result: any) {
    result.display = "";
    this.websocketService.updateResult(result);
  }

  // change the current result's display status to 'junked'
  public junkResult(result: any) {
    result.display = "junked";
    this.websocketService.updateResult(result);
  }

  // Start the download of data
  public initDownload(record: any) {

    // console.log("initDownload", record);

    // Signal that the request has been made
    const snackBarRef = this.snackBar.open("Download request submitted", "Ok", {
      duration: 2000,
    });

    // Make the request
    this.restService
      .getDownloadByHash(record.hash, record.path);

    // // Make the request
    // this.restService
    //   .getDownloadById(record._id, record.path);
    //   // .subscribe(result => {}, error => {});
  }
}
