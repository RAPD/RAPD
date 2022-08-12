import { Component,
  Inject,
  OnInit } from "@angular/core";
import { UntypedFormControl,
  UntypedFormGroup,
  Validators } from "@angular/forms";
import { MAT_DIALOG_DATA, MatDialog, MatDialogRef } from "@angular/material/dialog";
import { MatSnackBar } from "@angular/material/snack-bar";

import { DialogNewProjectComponent } from "../../../shared/components/dialog-new-project/dialog-new-project.component";
import { GlobalsService } from "../../../shared/services/globals.service";
import { RestService } from "../../../shared/services/rest.service";

@Component({
  selector: 'app-merge-dialog',
  templateUrl: './merge-dialog.component.html',
  styleUrls: ['./merge-dialog.component.css']
})
export class MergeDialogComponent implements OnInit {

  public submitted: boolean = false;
  public submitError: string = "";
  public metric: string = "CC";
  public mergeForm: UntypedFormGroup = new UntypedFormGroup({
    cutoff: new UntypedFormControl("Automatic"),
    description: new UntypedFormControl("", Validators.required),
    metric: new UntypedFormControl("CC", Validators.required),
    project: new UntypedFormControl("", Validators.required),
    resolution: new UntypedFormControl("Automatic"),
  });

  // Projects for the group that owns the session
  public projects = [];

  // Restrict the ability to execute the proces
  public executeDisabled = true;

  constructor(private globalsService: GlobalsService,
              private restService: RestService,
              public dialogRef: MatDialogRef<MergeDialogComponent>,
              private newProjectDialog: MatDialog,
              @Inject(MAT_DIALOG_DATA) public data: any,
              public snackBar: MatSnackBar) {}

  ngOnInit(): void {

    console.log(this.data);

    // Register for changes
    this.onChanges();

    // Get the projects for the current group
    this.getProjects(this.data[0].process.session_id);
  }

  private onChanges(): void {

    this.mergeForm.valueChanges.subscribe((val) => {
      console.log("onChanges", val);

      this.metric = val.metric;

      if ((val.description !== '') && (val.project !== '')) {
        this.executeDisabled = false;
      } else {
        this.executeDisabled = true;
      }
    });
  }

  private getProjects(sessionId: string) {
    this.restService.getProjectsBySession(sessionId).subscribe((parameters) => {
      console.log(parameters);
      if (parameters.success === true) {
        this.projects = parameters.result;
        if (this.data.current_project_id) {
          this.mergeForm.patchValue({project:this.data.current_project_id});
        }
      }
    });
  }

  public submitMerge() {

    // Collect data from merge form
    const mergeFormData = this.mergeForm.value;
    const mergeData = {
      cutoff: -1,
      description: mergeFormData.description,
      metric: mergeFormData.metric,
      project: mergeFormData.project,
      resolution: -1,
    };
    if (! isNaN(parseFloat(mergeFormData.cutoff))) {
      mergeData.cutoff = parseFloat(mergeFormData.cutoff);
    }
    if (! isNaN(parseFloat(mergeFormData.resolution))) {
      mergeData.resolution = parseFloat(mergeFormData.resolution);
    }
    // console.log(mergeData);

    // Collect parent_ids into one variable
    const parentIds = this.data.map((x: any) => {return x._id});

    // Start to make the request object
    const request: any = {
      command: "MERGE",
      data: false,
      preferences: Object.assign(
        this.data[0].preferences,
        mergeData
      ),
      process: {
        // image_id: undefined,
        parent_id: 'multiple',
        parent_ids: parentIds,
        // TODO
        repr: "Merge",
        // run_id: this.data.process.run_id,
        session_id: this.data[0].process.session_id,
        status: 0,
        type: "plugin",
      },
      site_parameters: false,
    };
    delete request.preferences.xdsinp;
    console.log(request);

    // Send to REST service and notfy via snackbar
    this.submitted = true;
    this.restService.submitJob(request).subscribe(parameters => {
      console.log(parameters);
      if (parameters.success === true) {
        const snackBarRef = this.snackBar.open(
          "Merge request submitted",
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
