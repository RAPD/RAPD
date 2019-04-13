import { Component,
         Inject,
         OnInit } from "@angular/core";
import { FormControl,
         FormGroup,
         Validators } from "@angular/forms";
import { MAT_DIALOG_DATA,
         MatDialog,
         MatDialogRef,
         MatSnackBar } from "@angular/material";

import * as moment from "moment-mini";

import { DialogNewProjectComponent } from "../../../shared/components/dialog-new-project/dialog-new-project.component";
import { GlobalsService } from "../../../shared/services/globals.service";
import { RestService } from "../../../shared/services/rest.service";

@Component({
  selector: "app-reintegrate-dialog",
  templateUrl: "./reintegrate-dialog.component.html",
  styleUrls: ["./reintegrate-dialog.component.css"]
})
export class ReintegrateDialogComponent implements OnInit {
  public submitted: boolean = false;
  public submit_error: string = "";
  public model: any;
  public reintegrateForm: FormGroup;

  public sample_types = [
    { val: "protein", label: "Protein" },
    { val: "dna", label: "DNA" },
    { val: "rna", label: "RNA" },
    { val: "peptide", label: "Peptide" }
  ];

  public spacegroup_deciders = [
    { val: "auto", label: "Automatic" },
    { val: "xds", label: "XDS" },
    { val: "pointless", label: "Pointless" }
  ];

  // Projects for the group that owns the session
  public projects = [];

  constructor(
    public globalsService: GlobalsService,
    private restService: RestService,
    private newProjectDialog: MatDialog,
    public dialogRef: MatDialogRef<ReintegrateDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any,
    public snackBar: MatSnackBar
  ) {}

  public ngOnInit() {

    console.log(this.data);

    // this.model = {
    //   end_frame: this.data.preferences.end_frame,
    //   hi_res: this.data.preferences.hi_res,
    //   low_res: this.data.preferences.low_res,
    //   rounds_polishing: this.data.preferences.rounds_polishing || 1,
    //   spacegroup: this.data.preferences.spacegroup || 0,
    //   spacegroup_decider: this.data.preferences.spacegroup_decider || "auto",
    //   start_frame: this.data.preferences.start_frame || 1,
    // };

    // if (! this.data.preferences.spacegroup) {
    //   this.model.spacegroup = 0;
    // }

    // if (! this.data.preferences.low_res) {
    //   this.model.low_res = "None";
    // }

    // if (! this.data.preferences.hi_res) {
    //   this.model.hi_res = "None";
    // }

    // Figure out end frame from repr - a bit of a kludge, need to improve
    let endFrame;
    if (! this.data.preferences.end_frame) {
      const repr = this.data.process.repr;
      endFrame = parseInt(repr.slice(repr.indexOf("[")+1,repr.indexOf("]")).split("-")[1], 10);
    }

    this.reintegrateForm = new FormGroup({
      description: new FormControl(""),
      end_frame: new FormControl(endFrame),
      hi_res: new FormControl(this.data.preferences.hi_res || undefined),
      low_res: new FormControl(this.data.preferences.low_res || null),
      project: new FormControl("", Validators.required),
      rounds_polishing: new FormControl(this.data.preferences.rounds_polishing || 1),
      sample_type: new FormControl(),
      spacegroup: new FormControl(this.data.preferences.spacegroup || 0),
      spacegroup_decider: new FormControl(this.data.preferences.spacegroup_decider || "auto"),
      start_frame: new FormControl(this.data.preferences.start_frame || 1),
    });

    // Handle changes of the form
    this.onChanges();

    // Get the projects for the current group
    this.getProjects(this.globalsService.currentSession);
  }

  private onChanges(): void {

    const self = this;

    this.reintegrateForm.valueChanges.subscribe((val) => {
      console.log("onChanges", val);

      // New project
      if (val.project === -1) {
        const newProjectDialogRef = this.newProjectDialog.open(DialogNewProjectComponent);
        newProjectDialogRef.componentInstance.dialog_title = "Create New Project";
        newProjectDialogRef.afterClosed().subscribe((result) => {
          console.log(result);
          if (result) {
            if (result.success === true) {
              self.projects.push(result.project);
              self.reintegrateForm.controls["project"].setValue(result.project._id);
            }
          } else {
            self.reintegrateForm.controls["project"].reset();
          }
        });
      }

      // // Enable execute button when conditions are correct
      // if (val.pdb_id.length > 3 || val.selected_pdb != 0) {
      //   self.executeDisabled = false;
      // } else {
      //   self.executeDisabled = true;
      // }

      // if (val.project != 0) {
      //   self.executeDisabled = false;
      // } else {
      //   self.executeDisabled = true;
      // }
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

  private submitReintegrate() {

    // Tweak repr in case images have changed
    const formData = this.reintegrateForm.value;
    if ((this.data.preferences.start_frame !== formData.start_frame) &&
    (this.data.preferences.end_frame !== formData.end_frame)) {
      false;
    }

    // Start to make the request object
    const request: any = {
      command: "REINTEGRATE",
      data: false,
      preferences: Object.assign(
        this.data.preferences,
        this.reintegrateForm.value
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

    // Update the preferences with the form values
    // request.preferences = Object.assign(this.data.preferences, this.reintegrate_form.value);

    // Debugging
    console.log(request);

    this.submitted = true;
    this.restService.submitJob(request).subscribe((parameters) => {
      console.log(parameters);
      if (parameters.success === true) {
        const snackBarRef = this.snackBar.open(
          "Reintegrate request submitted",
          "Ok",
          {
            duration: 10000,
          }
        );
        this.dialogRef.close(parameters);
      } else {
        this.submit_error = parameters.error;
      }
    });
  }
}
