import { Component, Inject, OnInit } from "@angular/core";

import {
  MAT_DIALOG_DATA,
  MatDialog,
  MatDialogRef,
  MatSnackBar
} from "@angular/material";

@Component({
  selector: "app-sad-dialog",
  templateUrl: "./sad-dialog.component.html",
  styleUrls: ["./sad-dialog.component.css"]
})
export class SadDialogComponent implements OnInit {
  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    public dialogRef: MatDialogRef<SadDialogComponent>
  ) {}

  public ngOnInit() {}
}
