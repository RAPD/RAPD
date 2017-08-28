import { Component,
         Inject,
         OnInit } from '@angular/core';
import { MdDialogRef,
         MdDialog,
         MD_DIALOG_DATA } from '@angular/material';

@Component({
  selector: 'app-header-dialog',
  templateUrl: './header-dialog.component.html',
  styleUrls: ['./header-dialog.component.css']
})
export class HeaderDialogComponent implements OnInit {

  constructor(public dialogRef: MdDialogRef<HeaderDialogComponent>,
              @Inject(MD_DIALOG_DATA) public data: any) { }

  ngOnInit() {
    console.log(this.data);
  }

  exitDialog() {
    this.dialogRef.close();
  }

}
