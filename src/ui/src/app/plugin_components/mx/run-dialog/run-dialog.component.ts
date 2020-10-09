import { Component,
         Inject,
         OnInit } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';

import { RestService } from '../../../shared/services/rest.service';

@Component({
  selector: 'app-run-dialog',
  templateUrl: './run-dialog.component.html',
  styleUrls: ['./run-dialog.component.css']
})
export class RunDialogComponent implements OnInit {

  public objectKeys = Object.keys;
  public image_data:any;
  public run_data:any;

  constructor(public dialogRef: MatDialogRef<RunDialogComponent>,
              private rest_service: RestService,
              @Inject(MAT_DIALOG_DATA) public data: any) { }

  ngOnInit() {
    // console.log(this.data);

    this.rest_service.getImageData(this.data.image_id)
                     .subscribe(
                       image_data => this.image_data=image_data,
                       error => console.error(error));

    this.rest_service.getRunData(this.data.run_id)
                     .subscribe(
                       run_data => this.run_data=run_data,
                       error => console.error(error));
  }

}
