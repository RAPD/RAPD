import { Component,
  Inject,
  OnInit } from "@angular/core";
import { FormControl,
  FormGroup,
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
  public mergeForm: FormGroup = new FormGroup({
    cutoff: new FormControl("Automatic"),
    description: new FormControl("", Validators.required),
    metric: new FormControl("CC", Validators.required),
    project: new FormControl("", Validators.required),
    resolution: new FormControl("Automatic"),
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

    // Collect data from merrge form
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

    console.log(mergeData);

    // // Start to make the request object
    // const request: any = {
    //   command: "MERGE",
    //   data: false,
    //   preferences: Object.assign(
    //     this.data[0].preferences,
    //     this.mergeForm.value
    //   ),
    //   process: {
    //     image_id: this.data.process.image_id,
    //     parent_id: this.data._id,
    //     repr: this.data.process.repr,
    //     run_id: this.data.process.run_id,
    //     session_id: this.data.process.session_id,
    //     status: 0,
    //     type: "plugin",
    //   },
    //   site_parameters: false,
    // };

  }

}
