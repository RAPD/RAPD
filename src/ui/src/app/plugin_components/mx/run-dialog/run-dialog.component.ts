import { Component,
         Inject,
         OnInit } from '@angular/core';
import { MdDialogRef,
         MD_DIALOG_DATA } from '@angular/material';


@Component({
  selector: 'app-run-dialog',
  templateUrl: './run-dialog.component.html',
  styleUrls: ['./run-dialog.component.css']
})
export class RunDialogComponent implements OnInit {

  constructor(public dialogRef: MdDialogRef<RunDialogComponent>,
              @Inject(MD_DIALOG_DATA) public data: any) { }

  ngOnInit() {
    console.log(this.data);
  }

}
