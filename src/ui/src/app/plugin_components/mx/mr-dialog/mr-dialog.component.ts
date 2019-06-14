import { Component,
         Inject,
         OnInit } from "@angular/core";
import { FormControl,
         FormGroup,
         Validators } from "@angular/forms";
import { MAT_DIALOG_DATA, MatDialog, MatDialogRef } from "@angular/material/dialog";
import { MatSnackBar } from "@angular/material/snack-bar";

import * as moment from "moment-mini";
import { FileUploader } from "ng2-file-upload";

import { DialogNewProjectComponent } from "../../../shared/components/dialog-new-project/dialog-new-project.component";
import { GlobalsService } from "../../../shared/services/globals.service";
import { RestService } from "../../../shared/services/rest.service";

@Component({
  selector: "app-mr-dialog",
  templateUrl: "./mr-dialog.component.html",
  styleUrls: ["./mr-dialog.component.css"]
})
export class MrDialogComponent implements OnInit {
  public submitted: boolean = false;
  public submitError: string = "";
  public model: any;
  public mrForm: FormGroup;
  public uploader: FileUploader;

  // Projects for the group that owns the session
  public projects = [];

  // List of PDB files uploaded by this group
  public uploadedPdbs = [];

  public executeDisabled = true;
  public pdbSelectDisabled = false;

  constructor(
    private globalsService: GlobalsService,
    private restService: RestService,
    public dialogRef: MatDialogRef<MrDialogComponent>,
    private newProjectDialog: MatDialog,
    @Inject(MAT_DIALOG_DATA) public data: any,
    public snackBar: MatSnackBar) {}

  public ngOnInit() {

    console.log(this.data);

    // Create form
    this.mrForm = new FormGroup({
      description: new FormControl(""),
      number_molecules: new FormControl(0),
      pdb_id: new FormControl(this.data.preferences.pdb_id || ""),
      project: new FormControl("", Validators.required),
      selected_pdb: new FormControl(0),
    });
    this.onChanges();

    // Init the file uploader
    this.initUploader();

    // Get the uploads for the current group
    this.getUploads(this.globalsService.currentSession);

    // Get the projects for the current group
    this.getProjects(this.globalsService.currentSession);
  }

  private onChanges(): void {

    const self = this;

    this.mrForm.valueChanges.subscribe((val) => {
      console.log("onChanges", val);

      // New project
      if (val.project === -1) {
        const newProjectDialogRef = this.newProjectDialog.open(DialogNewProjectComponent);
        newProjectDialogRef.componentInstance.dialog_title = "Create New Project";
        newProjectDialogRef.afterClosed().subscribe((result) => {
          if (result) {
            if (result.success === true) {
              self.projects.push(result.project);
              self.mrForm.controls["project"].setValue(result.project._id);
            }
          } else {
            self.mrForm.controls["project"].reset();
          }
        });
      }

      // Disable/Enable the PDB select and upload based on the input
      if (val.pdb_id) {
        this.pdbSelectDisabled = true;
      } else {
        this.pdbSelectDisabled = false;
      }

      // Enable execute button when conditions are correct
      if (val.pdb_id.length > 3 || val.selected_pdb != 0) {
        self.executeDisabled = false;
      } else {
        self.executeDisabled = true;
      }

      if (val.project != 0) {
        self.executeDisabled = false;
      } else {
        self.executeDisabled = true;
      }
    });
  }

  private getUploads(session_id: string) {

    this.restService.getUploadedPdbsBySession(session_id).subscribe(parameters => {
      // console.log(parameters);
      if (parameters.success === true) {
        this.uploadedPdbs = parameters.result;
      }
    });
  }

  private getProjects(session_id: string) {

    this.restService.getProjectsBySession(session_id).subscribe(parameters => {
      // console.log(parameters);
      if (parameters.success === true) {
        this.projects = parameters.result;
      }
    });
  }

  private initUploader() {
    let self = this;

    this.uploader = new FileUploader({
      additionalParameter: {session_id:this.globalsService.currentSession},
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
        // Add to pdbs on file
        this.uploadedPdbs.unshift(res.pdb);
        this.mrForm.controls["selected_pdb"].setValue(res.pdb._id);
        // Pop the snackbar
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

  private submitMr() {

    // let formData = this.mrForm.value;
    // console.log(formData);
    // console.log(this.data);

    // Start to make the request object
    const request: any = {
      command: "MR",
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

    // Cleanup the preferences
    if ("xdsinp" in request.preferences) {
      delete request.preferences.xdsinp;
    }
    if ("analysis" in request.preferences) {
      delete request.preferences.analysis;
    }

    // Debugging
    console.log(request);

    this.submitted = true;
    this.restService.submitJob(request).subscribe(parameters => {
      console.log(parameters);
      if (parameters.success === true) {
        let snackBarRef = this.snackBar.open(
          "Reintegrate request submitted",
          "Ok",
          {
            duration: 10000,
          }
        );
        // Close the dialog
        this.dialogRef.close(parameters);
      } else {
        this.submitError = parameters.error;
      }
    });
  }
}
