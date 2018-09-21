import { Component, OnInit, ViewContainerRef } from "@angular/core";
import { Router } from "@angular/router";
import {
  MatDialog,
  MatDialogConfig,
  MatDialogRef,
  MatToolbarModule
} from "@angular/material";

import { RestService } from "../shared/services/rest.service";
import { Project } from "../shared/classes/project";
import { DialogNewProjectComponent } from "../shared/components/dialog-new-project/dialog-new-project.component";
import { ConfirmDialogComponent } from "../shared/dialogs/confirm-dialog/confirm-dialog.component";
// import { FileUploadModule } from 'ng2-file-upload';

@Component({
  selector: "app-projectspanel",
  templateUrl: "./projectspanel.component.html",
  styleUrls: ["./projectspanel.component.css"]
})
export class ProjectspanelComponent implements OnInit {
  projects: Project[] = [];
  dialogRef: MatDialogRef<DialogNewProjectComponent>;

  // File uploader
  // public uploader:FileUploader = new FileUploader({url: 'https://evening-anchorage-3159.herokuapp.com/api/'});

  constructor(
    private rest_service: RestService,
    public viewContainerRef: ViewContainerRef,
    public dialog: MatDialog,
    private router: Router
  ) {}

  ngOnInit() {
    this.getProjects();
  }

  getProjects() {
    // TODO
    this.rest_service.getProjects().subscribe(parameters => {
      console.log(parameters);
      this.projects = parameters;
    });
  }

  newProject() {
    let project = new Project();

    project._id = undefined;
    project.actions = [];
    project.creator = undefined;
    project.created = undefined;
    project.description = undefined;
    project.group = undefined;
    project.last_action = undefined;
    project.last_timestamp = undefined;
    project.project_type = "mx";
    project.results = [];
    project.title = undefined;

    this.editProject(project, "Create Project");
  }

  // Deleting a project
  deleteProject(project: Project) {
    // Open the confirmation dialog
    let config = new MatDialogConfig();
    config.viewContainerRef = this.viewContainerRef;

    this.dialogRef = this.dialog.open(ConfirmDialogComponent, config);
    this.dialogRef.componentInstance.data = {
      message: "Are you sure? Deleting a project is permenant.",
      title: "Confirm Deletion"
    };

    this.dialogRef.afterClosed().subscribe(result => {
      // Go ahead and "delete" the project
      if (result) {
        project.status = "hidden";
        this.rest_service.submitProject(project).subscribe(params => {
          console.log(params);
          // A problem connecting to REST server
          // Submitted is over
          // this.submitted = false;
          // this.submit_error = params.error;
          // if (params.success) {
          //   this.dialogRef.close(params);
          // } else {
          //   this.submit_error = params.message;
          // }
        });
      }
    });
  }

  editProject(project, dialog_title: string) {
    if (dialog_title !== "Create Project") {
      dialog_title = "Edit Project";
    }

    let config = new MatDialogConfig();
    config.viewContainerRef = this.viewContainerRef;

    this.dialogRef = this.dialog.open(DialogNewProjectComponent, config);
    this.dialogRef.componentInstance.project = project;
    this.dialogRef.componentInstance.dialog_title = dialog_title;

    this.dialogRef.afterClosed().subscribe(result => {
      if (result) {
        if (result.success === true) {
          if (result.operation === "delete") {
            this.removeProject(result._id);
          } else {
            this.addProject(result.project);
          }
        }
      }
    });
  }

  //
  // Methods for manipulating the this.projects array
  //
  addProject(new_project: Project) {
    // If the user already exists, replace it
    let index = this.projects.findIndex(
      project => project._id === new_project._id
    );
    if (index !== -1) {
      this.projects.splice(index, 1, new_project);
    } else {
      this.projects.unshift(new_project);
    }
  }

  removeProject(_id: string) {
    // If the user already exists, replace it
    let index = this.projects.findIndex(project => project._id === _id);
    if (index !== -1) {
      this.projects.splice(index, 1);
    }
  }

  selectProject(project: any) {
    this.router.navigate(["project-" + project.project_type, project._id]);
  }
}
