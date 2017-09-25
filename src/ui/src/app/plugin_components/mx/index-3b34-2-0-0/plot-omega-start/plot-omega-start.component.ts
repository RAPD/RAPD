import { Component,
         Inject,
         OnInit,
         ViewChild } from '@angular/core';
import { MdDialogRef,
         MatDialog,
         MAT_DIALOG_DATA } from '@angular/material';
import { BaseChartDirective } from 'ng2-charts';

@Component({
  selector: 'app-plot-omega-start',
  templateUrl: './plot-omega-start.component.html',
  styleUrls: ['./plot-omega-start.component.css']
})
export class PlotOmegaStartComponent implements OnInit {

  // @ViewChild(BaseChartDirective) private Chart: BaseChartDirective;

  constructor(public dialogRef: MdDialogRef<PlotOmegaStartComponent>,
              @Inject(MAT_DIALOG_DATA) public data: any) { }

  ngOnInit() {
    console.log(this.data);
    // console.log(this.Chart);
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


  exitPlot() {
    this.dialogRef.close();
    // this._ngZone.run(() => this.dialogRef.close());
  }

}
