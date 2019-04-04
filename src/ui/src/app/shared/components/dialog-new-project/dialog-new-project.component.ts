import { Component, Input, OnInit } from "@angular/core";

import { FormGroup, FormControl } from "@angular/forms";

import { MatDialogRef, MAT_DIALOG_DATA } from "@angular/material";

import { Project } from "../../classes/project";
import { User } from "../../classes/user";

import { GlobalsService } from "../../../shared/services/globals.service";
import { RestService } from "../../services/rest.service";

@Component({
  selector: "app-dialog-new-project",
  styleUrls: ["./dialog-new-project.component.css"],
  templateUrl: "./dialog-new-project.component.html",
})
export class DialogNewProjectComponent implements OnInit {
  public user: User;
  public profile: any;
  public submit_error: string;
  public submitted: boolean = false;
  @Input() project: Project;
  @Input() dialog_title: string;
  public model: Project;
  public project_form: FormGroup;

  constructor(
    private globalsService: GlobalsService,
    private restService: RestService,
    public dialogRef: MatDialogRef<DialogNewProjectComponent>
  ) {}

  public ngOnInit() {

    // Get the user profile
    this.user = JSON.parse(localStorage.getItem("profile"));

    // Load the model with project
    // this.model = Object.assign({}, this.project);
    // console.log(this.project);

    // Create the form group
    this.project_form = new FormGroup({
      description: new FormControl(),
      // group: new FormControl(),
      project_type: new FormControl(),
      session: new FormControl(this.globalsService.currentSession),
      title: new FormControl(),
    });
  }

  private submitProject() {
    this.submitted = true;
    this.restService.submitProject(this.project_form.value).subscribe((params) => {
      console.log(params);
      // A problem connecting to REST server
      // Submitted is over
      this.submitted = false;
      this.submit_error = params.error;
      if (params.success) {
        this.dialogRef.close(params);
      } else {
        this.submit_error = params.message;
      }
    });
  }

  private deleteProject() {
    this.submitted = true;

    // Use REST service
    this.restService.deleteProject(this.project._id).subscribe(params => {
      // console.log(params);
      this.submitted = false;
      if (params.success === true) {
        this.dialogRef.close(params);
      } else {
        this.submit_error = params.message;
      }
    });
  }
}
