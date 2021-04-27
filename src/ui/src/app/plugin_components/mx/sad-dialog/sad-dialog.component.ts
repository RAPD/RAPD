import { Component, Inject, OnInit } from "@angular/core";
import { FormControl, FormGroup, Validators } from "@angular/forms";
import { MAT_DIALOG_DATA, MatDialog, MatDialogRef } from "@angular/material/dialog";
import { MatSnackBar } from "@angular/material/snack-bar";

import { DialogNewProjectComponent } from "../../../shared/components/dialog-new-project/dialog-new-project.component";
import { SequenceDialogComponent } from "../../../shared/dialogs/sequence-dialog/sequence-dialog.component";
import { GlobalsService } from "../../../shared/services/globals.service";
import { RestService } from "../../../shared/services/rest.service";

@Component({
  selector: "app-sad-dialog",
  templateUrl: "./sad-dialog.component.html",
  styleUrls: ["./sad-dialog.component.css"],
})
export class SadDialogComponent implements OnInit {

  public submitted: boolean = false;
  public submitError: string = "";

  public sadForm: FormGroup = new FormGroup({
    description: new FormControl("", Validators.required),
    element: new FormControl("Se"),
    hires_cutoff: new FormControl("0"),
    number_atoms: new FormControl(0),
    number_disulfides: new FormControl(0),
    number_trials: new FormControl(1024),
    project: new FormControl("", Validators.required),
    sequence: new FormControl(0),
  });

  // Form appearance
  isSulfur = false;
  zeroAtoms = true;
  zeroCutoff = true;

  // Projects for the group that owns the session
  public projects: string[] = [];

  // Sequences for the group that owns the session
  public sequences: string[] = [];

  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    public dialogRef: MatDialogRef<SadDialogComponent>,
    public globalsService: GlobalsService,
    public snackBar: MatSnackBar,
    private restService: RestService,
    private newProjectDialog: MatDialog,
    private newSequenceDialog: MatDialog
  ) {}

  public ngOnInit() {

    this.onChanges();

    // Get the projects for the current group
    this.getProjects(this.data.process.session_id);
  }

  private onChanges(): void {

    const self = this;

    this.sadForm.valueChanges.subscribe((val) => {

      // console.log("onChanges", val);

      // Disulfides
      this.isSulfur = (val.element === "S");

      // Atoms
      this.zeroAtoms = (val.number_atoms === 0);

      // Hires cutoff
      this.zeroCutoff = (val.hires_cutoff.sstrip() === "0");

      // New project
      if (val.project === -1) {
        const newProjectDialogRef = this.newProjectDialog.open(DialogNewProjectComponent);
        newProjectDialogRef.componentInstance.dialog_title = "Create New Project";
        newProjectDialogRef.afterClosed().subscribe((result) => {
          if (result) {
            if (result.success === true) {
              self.projects.push(result.project);
              self.sadForm.controls.project.setValue(result.project._id);
            }
          } else {
            self.sadForm.controls.project.reset();
          }
        });
      }

      // New sequence
      if (val.sequence === -1) {
        const newSequenceDialogRef = this.newSequenceDialog.open(SequenceDialogComponent);
        newSequenceDialogRef.componentInstance.dialogTitle = "Enter New Sequence";
        newSequenceDialogRef.afterClosed().subscribe((result) => {
          if (result) {
            if (result.success === true) {
              self.projects.push(result.project);
              self.sadForm.controls.sequence.setValue(result.project._id);
            }
          } else {
            self.sadForm.controls.sequence.setValue(0);
          }
        });
      }
  })
}

  private getProjects(sessionId: string) {
    this.restService.getProjectsBySession(sessionId).subscribe(parameters => {
      if (parameters.success === true) {
        this.projects = parameters.result;
        if (this.data.current_project_id) {
          this.sadForm.patchValue({project:this.data.current_project_id});
        }
      }
    });
  }

  private submitSad() {

    let formData = this.sadForm.value;
    console.log(formData);
    console.log(this.data);

    // Start to make the request object
    const request: any = {
      command: "SAD",
      data: false,
      preferences: Object.assign(
        this.data.preferences,
        this.sadForm.value
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
    if ('xdsinp' in request.preferences) {
      delete request.preferences.xdsinp;
    }
    if ('analysis' in request.preferences) {
      delete request.preferences.analysis;
    }
    if (isNaN(request.preferences.hires_cutoff)) {
      request.preferences.hires_cutoff = 0;
    } else {
      request.preferences.hires_cutoff = parseFloat(request.preferences.hires_cutoff);
    }

    // Debugging
    console.log(request);

    this.submitted = true;
    this.restService.submitJob(request).subscribe(parameters => {
      // console.log(parameters);
      if (parameters.success === true) {
        const snackBarRef = this.snackBar.open(
          "SAD request submitted",
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
