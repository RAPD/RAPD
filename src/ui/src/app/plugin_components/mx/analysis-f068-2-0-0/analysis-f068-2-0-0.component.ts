import { Component,
         Input,
         OnInit } from "@angular/core";

import { GlobalsService } from "../../../shared/services/globals.service";

@Component({
  selector: "app-analysis-f068-2-0-0",
  styleUrls: ["./analysis-f068-2-0-0.component.css", ],
  templateUrl: "./analysis-f068-2-0-0.component.html",
})
export class AnalysisF068200Component implements OnInit {
  @Input() public result: any;
  public objectKeys = Object.keys;
  public selected_plot: string;

  // Data object for plots
  public data: any = {
    lineChartType: "line",
    lineChartOptions: {
      animation: {
        duration: 500
      },
      elements: {
        line: {
          tension: 0 // disables bezier curves
        }
      },
      legend: {
        display: true,
        position: "right",
        labels: {
          boxWidth: 3
        }
      },
      responsive: true,
      scales: {
        yAxes: [
          {
            scaleLabel: {
              display: true,
              labelString: ""
            }
          }
        ],
        xAxes: [
          {
            afterTickToLabelConversion: undefined,
            scaleLabel: {
              display: true,
              labelString: ""
            }
          }
        ]
      }
    }
  };

  constructor(private globals_service: GlobalsService) {}

  public ngOnInit() {

    console.log(this.result);

    if (this.result.results.parsed.xtriage.plots) {
      if ("Intensity plots" in this.result.results.parsed.xtriage.plots) {
        this.selected_plot = "Intensity plots";
        this.setPlot("Intensity plots");
      }
    }
  }

  public setPlot(plotKey: string) {

    // Simplify
    let plotData = this.result.results.parsed.xtriage.plots[plotKey];

    // Common vars
    this.data.xs = plotData.x_data;
    this.data.ys = plotData.y_data;
    this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString =
      plotData.parameters.xlabel;
    this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString =
      plotData.parameters.ylabel;

    switch (plotKey) {
      case "Intensity plots":
        // Make sure the x labels are only 2 places...
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = function(
          data
        ) {
          var xLabels = data.ticks;
          xLabels.forEach(function(labels, i) {
            xLabels[i] = parseFloat(xLabels[i]).toFixed(2);
          });
        };
        // Change the label
        this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString =
          "Resolution (\u00C5)";
        this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString =
          "Intensity";
        break;

      case "Measurability of Anomalous signal":

        // Create the minimum signal line
        const dataLen = this.data.ys[0].data.length;
        const minLineData = {
          data: new Array(dataLen).fill(0.05),
          label: "Min Level",
          pointRadius: 0,
        };
        this.data.ys.push(minLineData);

        // Change x label
        this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString =
          "Resolution (\u00C5)";
        // Show only 2 places in x axis
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = function(
          data
        ) {
          var xLabels = data.ticks;
          xLabels.forEach(function(labels, i) {
            xLabels[i] = parseFloat(xLabels[i]).toFixed(2);
          });
        };
        break;

      case "NZ test":
        // No tick conversion
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined;
        break;

      case "L test, acentric data":
        // No tick conversion
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined;
        break;

      default:
        break;
      // this.data = false;
    }

    console.log(this.data.ys);
  }
}
