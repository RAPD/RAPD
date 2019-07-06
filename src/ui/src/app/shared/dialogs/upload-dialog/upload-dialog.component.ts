import { Component,
         Inject,
         OnInit } from '@angular/core';

import { MatDialogRef,
         MAT_DIALOG_DATA } from '@angular/material';

import { FileUploader } from 'ng2-file-upload';

import { GlobalsService } from '../../services/globals.service';

@Component({
  selector: 'app-upload-dialog',
  templateUrl: './upload-dialog.component.html',
  styleUrls: ['./upload-dialog.component.css']
})
export class UploadDialogComponent implements OnInit {

  public uploader:FileUploader;

  constructor(public dialogRef: MatDialogRef<UploadDialogComponent>,
              @Inject(MAT_DIALOG_DATA) public data: any,
              private globals_service: GlobalsService) { }

  ngOnInit() {
    console.log(this.data);
    
    this.uploader = new FileUploader({
      url: this.globals_service.site.restApiUrl + "/upload",
      autoUpload: true,
    });
    //override the onAfterAddingfile property of the uploader so it doesn't authenticate with //credentials.
    this.uploader.onAfterAddingFile = (file)=> { file.withCredentials = false; };
    //overide the onCompleteItem property of the uploader so we are 
    //able to deal with the server response.
    this.uploader.onCompleteItem = (item:any, response:any, status:any, headers:any) => {
         console.log("ImageUpload:uploaded:", item, status, response);
     };
  }

  onFileSelected() {
    console.log('onFileSelected');
    console.log(this.uploader.queue);
  }

}
