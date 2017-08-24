import { Component, OnInit } from '@angular/core';
import { MdDialogRef,
         MdDialog,
         MD_DIALOG_DATA } from '@angular/material';
@Component({
  selector: 'app-plot-omega-start',
  templateUrl: './plot-omega-start.component.html',
  styleUrls: ['./plot-omega-start.component.css']
})
export class PlotOmegaStartComponent implements OnInit {

  constructor(public dialogRef: MdDialogRef<PlotOmegaStartComponent>) { }

  ngOnInit() {

  }

  exitPlot() {
    this.dialogRef.close();
    // this._ngZone.run(() => this.dialogRef.close());
  }

}
