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
  styleUrls: ["./sad-dialog.component.css"]
})
export class SadDialogComponent implements OnInit {
  public submitted: boolean = false;
  public submitError: string = "";
  public sadForm: FormGroup;

  // Projects for the group that owns the session
  public projects = [];

  // Sequences for the group that owns the session
  public sequences = [];

  constructor(
    private globalsService: GlobalsService,
    private restService: RestService,
    private newProjectDialog: MatDialog,
    private newSequenceDialog: MatDialog,
    @Inject(MAT_DIALOG_DATA) public data: any,
    public dialogRef: MatDialogRef<SadDialogComponent>,
    public snackBar: MatSnackBar
  ) {}

  public ngOnInit() {
    // Create form
    this.sadForm = new FormGroup({
      description: new FormControl(""),
      element: new FormControl("Se"),
      hires_cutoff: new FormControl(0),
      number_atoms: new FormControl(0),
      number_disulfides: new FormControl({value: 0, disabled: true}),
      number_trials: new FormControl(1024),
      project: new FormControl("", Validators.required),
      sequence: new FormControl(0),
    });
    this.onChanges();

    // Get the projects for the current group
    this.getProjects(this.globalsService.currentSessionId);
  }

  private onChanges(): void {

    const self = this;

    this.sadForm.valueChanges.subscribe((val) => {
      console.log("onChanges", val);

      // Disulfides
      if (val.element === "S") {
        if (this.sadForm.controls["number_disulfides"].disabled) {
          this.sadForm.controls["number_disulfides"].enable();
        }
      } else {
        if (val.number_disulfides > 0) {
          this.sadForm.controls["number_disulfides"].setValue(0);
        }
        if (this.sadForm.controls["number_disulfides"].enabled) {
          this.sadForm.controls["number_disulfides"].disable();
        }
      }

      // New project
      if (val.project === -1) {
        const newProjectDialogRef = this.newProjectDialog.open(DialogNewProjectComponent);
        newProjectDialogRef.componentInstance.dialog_title = "Create New Project";
        newProjectDialogRef.afterClosed().subscribe((result) => {
          if (result) {
            if (result.success === true) {
              self.projects.push(result.project);
              self.sadForm.controls["project"].setValue(result.project._id);
            }
          } else {
            self.sadForm.controls["project"].reset();
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
              self.sadForm.controls["sequence"].setValue(result.project._id);
            }
          } else {
            self.sadForm.controls["sequence"].setValue(0);
          }
        });
      }
  })
}

  private getProjects(session_id: string) {
    this.restService.getProjectsBySession(session_id).subscribe(parameters => {
      // console.log(parameters);
      if (parameters.success === true) {
        this.projects = parameters.result;
      }
    });
  }
}
