import { Component,
         Inject,
         OnInit } from '@angular/core';
import { MatDialogRef,
         MAT_DIALOG_DATA } from '@angular/material';
import { RestService } from '../../../shared/services/rest.service';

@Component({
  selector: 'app-header-dialog',
  templateUrl: './header-dialog.component.html',
  styleUrls: ['./header-dialog.component.css']
})
export class HeaderDialogComponent implements OnInit {

  public image_data:any;
  public error:any;

  constructor(public dialogRef: MatDialogRef<HeaderDialogComponent>,
              private rest_service: RestService,
              @Inject(MAT_DIALOG_DATA) public data: any) { }

  ngOnInit() {
    console.log(this.data);

    this.rest_service.getImageData(this.data.image_id)
                     .subscribe(
                       image_data => this.image_data=image_data,
                       error => this.error=error);
  }
}
