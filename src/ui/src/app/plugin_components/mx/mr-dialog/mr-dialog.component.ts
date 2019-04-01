import { Component, Inject, OnInit } from "@angular/core";
import { FormControl, FormGroup } from "@angular/forms";
import { MAT_DIALOG_DATA, MatDialogRef, MatSnackBar } from "@angular/material";

import { FileUploader } from "ng2-file-upload";

import * as moment from "moment-mini";
import { GlobalsService } from "../../../shared/services/globals.service";
import { RestService } from "../../../shared/services/rest.service";

@Component({
  selector: "app-mr-dialog",
  templateUrl: "./mr-dialog.component.html",
  styleUrls: ["./mr-dialog.component.css"]
})
export class MrDialogComponent implements OnInit {
  public submitted: boolean = false;
  public submit_error: string = "";
  public model: any;
  public mrForm: FormGroup;
  public uploader: FileUploader;

  // List of PDB files uploaded by this group
  private uploadedPdbs = [];

  private NUMBER_MOLECULES = [
    { val: 0, label: "Automatic" },
    { val: 1, label: "1" },
    { val: 2, label: "2" },
    { val: 3, label: "3" },
    { val: 4, label: "4" },
    { val: 5, label: "5" },
    { val: 6, label: "6" },
  ];

  constructor(
    private globalsService: GlobalsService,
    private restService: RestService,
    public dialogRef: MatDialogRef<MrDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any,
    public snackBar: MatSnackBar) {}

  public ngOnInit() {
    // console.log(this.data);

    // let self = this;

    console.log(this.globalsService.currentSession);

    // init the file uploader
    this.initUploader();

    this.model = {
      number_molecules: this.data.preferences.number_molecules || 0,
      pdb_id: this.data.preferences.pdb_id || "",
      selected_pdb: "",
    };

    this.mrForm = new FormGroup({
      number_molecules: new FormControl(),
      pdb_id: new FormControl(),
      selected_pdb: new FormControl(),
    });

    // Get the uploads for the current group
    this.getUploads(this.globalsService.currentSession);
  }

  private getUploads(session_id: string) {

    this.restService.getUploadedPdbsBySession(session_id).subscribe(parameters => {
      console.log(parameters);
      if (parameters.success === true) {
        this.uploadedPdbs = parameters.uploaded_pdbs;
      }
    });
  }

  private initUploader() {
    let self = this;

    this.uploader = new FileUploader({
      authToken: localStorage.getItem("access_token"),
      autoUpload: true,
      url: this.globalsService.site.restApiUrl + "/upload_pdb",
    });
    // override the onAfterAddingfile property of the uploader so it doesn't authenticate with //credentials.
    this.uploader.onAfterAddingFile = (file) => {
      file.withCredentials = false;
    };
    // overide the onCompleteItem property of the uploader so we are
    // able to deal with the server response.
    this.uploader.onCompleteItem = (
      item: any,
      response: any,
      status: any,
      headers: any
    ) => {
      console.log("PdbUpload:uploaded:", item, status, response);
      const res = JSON.parse(response);
      console.log(typeof(res));
      if (res.success === true) {
        const snackBarRef = self.snackBar.open(
          "File uploaded",
          "Ok",
          {
            duration: 5000,
          }
        );
      }
    };
  }

  private submitReintegrate() {
    /*
    command = {
                "command":"INTEGRATE",
                "process":{
                    "image_id":image1.get("_id"),
                    "parent_id":False,
                    "result_id":str(ObjectId()),
                    "run_id":run_data.get("_id"),
                    "session_id":session_id,
                    "status":0,
                    "type":"plugin"
                    },
                "directories":directories,
                "data": {
                    "image_data":image1,
                    "run_data":run_data
                },
                "site_parameters":self.site.BEAM_INFO[image1["site_tag"]],
                "preferences":{
                    "cleanup":False,
                    "json":False,
                    "exchange_dir":self.site.EXCHANGE_DIR,
                    "xdsinp":xdsinp
                },
            }
    */

    let formData = this.mrForm.value;
    console.log(formData);

    console.log(this.data);

    //

    // Tweak repr in case images have changed
    if ((this.data.preferences.start_frame !== formData.start_frame) &&
    (this.data.preferences.end_frame !== formData.end_frame)) {
      false;
    }


    // Start to make the request object
    let request: any = {
      command: "REINTEGRATE",
      data: false,
      preferences: Object.assign(
        this.data.preferences,
        this.mrForm.value
      ),
      process: {
        image_id: this.data.process.image_id,
        parent_id: this.data._id,
        repr: this.data.process.repr,
        run_id: this.data.process.run_id,
        session_id: this.data.process.session_id,
        status: 0,
        type: "plugin",
      },
      site_parameters: false,
    };

    // request.parent_result_id = this.data._id;

    // Update the preferences with the form values
    // request.preferences = Object.assign(this.data.preferences, this.reintegrate_form.value);

    // Debugging
    console.log(request);

    // this.submitted = true;
    // this.rest_service.submitJob(request).subscribe(parameters => {
    //   console.log(parameters);
    //   if (parameters.success === true) {
    //     let snackBarRef = this.snackBar.open(
    //       "Reintegrate request submitted",
    //       "Ok",
    //       {
    //         duration: 10000
    //       }
    //     );
    //     this.dialogRef.close(parameters);
    //   } else {
    //     this.submit_error = parameters.error;
    //   }
    // });
  }
}
