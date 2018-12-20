import {
  Component,
  Inject,
  Input,
  OnInit,
  ViewContainerRef
} from "@angular/core";
import { FormControl, FormGroup } from "@angular/forms";
import { MAT_DIALOG_DATA, MatDialog, MatDialogRef } from "@angular/material";

import { DialogNewProjectComponent } from "../../../shared/components/dialog-new-project/dialog-new-project.component";
import { RestService } from "../../../shared/services/rest.service";
import { Project } from "../../classes/project";

@Component({
  selector: "app-dialog-select-project",
  styleUrls: ["./dialog-select-project.component.css"],
  templateUrl: "./dialog-select-project.component.html",

})
export class DialogSelectProjectComponent implements OnInit {
  public projects: any;
  public submitError: string;
  public submitted: boolean = false;
  public model: any = { _id: "" };
  public projectForm: FormGroup;

  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    public dialogRef: MatDialogRef<DialogSelectProjectComponent>,
    private restService: RestService,
    private newProjectDialog: MatDialog
  ) {}

  public ngOnInit() {
    // Get available projects
    // TODO
    this.restService.getProjects().subscribe(
      (parameters) => {
        // console.log(parameters);
        this.projects = parameters.projects;
      }
    );

    // Create the form group
    this.projectForm = new FormGroup({
      _id: new FormControl(),
    });
    this.onChanges();
  }

  private onChanges(): void {

    const self = this;

    this.projectForm.valueChanges.subscribe((val) => {
      // console.log("onChanges", val);

      // New project
      if (val._id === -1) {
        const newProjectDialogRef = this.newProjectDialog.open(DialogNewProjectComponent);
        newProjectDialogRef.componentInstance.dialog_title = "New Project";
        newProjectDialogRef.afterClosed().subscribe((result) => {
          if (result) {
            console.log(result);
            if (result.success === true) {
              self.projects.push(result.project);
              self.model._id = result.project._id;
            }
          }
        });
      }
    });
  }

  private submitProjectSelection() {
    const formValue = this.projectForm.value;

    if (!formValue._id) {
      return false;
    }

    // Add the result to the form_value
    formValue.result = this.data;

    console.log(formValue);

    this.submitted = true;
    this.restService.addResultToProject(formValue).subscribe((parameters) => {
      console.log(parameters);
      // A problem connecting to REST server
      // Submitted is over
      this.submitted = false;

      if (parameters.success) {
        this.dialogRef.close(parameters.project);
      } else {
        this.submitError = parameters.message;
      }
    });
  }
}
