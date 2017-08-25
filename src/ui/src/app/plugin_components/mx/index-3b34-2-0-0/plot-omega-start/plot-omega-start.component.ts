import { Component,
         Inject,
         OnInit,
         ViewChild } from '@angular/core';
import { MdDialogRef,
         MdDialog,
         MD_DIALOG_DATA } from '@angular/material';
import { BaseChartDirective } from 'ng2-charts';

@Component({
  selector: 'app-plot-omega-start',
  templateUrl: './plot-omega-start.component.html',
  styleUrls: ['./plot-omega-start.component.css']
})
export class PlotOmegaStartComponent implements OnInit {

  // @ViewChild(BaseChartDirective) private Chart: BaseChartDirective;

  constructor(public dialogRef: MdDialogRef<PlotOmegaStartComponent>,
              @Inject(MD_DIALOG_DATA) public data: any) { }

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
    { // grey
      backgroundColor: 'rgba(148,159,177,0.2)',
      borderColor: 'rgba(148,159,177,1)',
      pointBackgroundColor: 'rgba(148,159,177,1)',
      pointBorderColor: '#fff',
      pointHoverBackgroundColor: '#fff',
      pointHoverBorderColor: 'rgba(148,159,177,0.8)'
    },
    { // dark grey
      backgroundColor: 'rgba(77,83,96,0.2)',
      borderColor: 'rgba(77,83,96,1)',
      pointBackgroundColor: 'rgba(77,83,96,1)',
      pointBorderColor: '#fff',
      pointHoverBackgroundColor: '#fff',
      pointHoverBorderColor: 'rgba(77,83,96,1)'
    },
    { // grey
      backgroundColor: 'rgba(148,159,177,0.2)',
      borderColor: 'rgba(148,159,177,1)',
      pointBackgroundColor: 'rgba(148,159,177,1)',
      pointBorderColor: '#fff',
      pointHoverBackgroundColor: '#fff',
      pointHoverBorderColor: 'rgba(148,159,177,0.8)'
    }
  ];
  public lineChartLegend:boolean = true;
  public lineChartType:string = 'line';


  exitPlot() {
    this.dialogRef.close();
    // this._ngZone.run(() => this.dialogRef.close());
  }

}
