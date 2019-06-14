import { Component, OnInit, ViewContainerRef } from "@angular/core";
import { MatDialog, MatDialogConfig, MatDialogRef } from "@angular/material/dialog";
import { MatToolbarModule } from "@angular/material/toolbar";
import { Router } from "@angular/router";


import { Project } from "../shared/classes/project";
import { DialogNewProjectComponent } from "../shared/components/dialog-new-project/dialog-new-project.component";
import { RestService } from "../shared/services/rest.service";
// import { FileUploadModule } from 'ng2-file-upload';

@Component({
  selector: "app-projectspanel",
  styleUrls: ["./projectspanel.component.css"],
  templateUrl: "./projectspanel.component.html",
})
export class ProjectspanelComponent implements OnInit {
  public projects: Project[] = [];
  private dialogRef: MatDialogRef<DialogNewProjectComponent>;

  // File uploader
  // public uploader:FileUploader = new FileUploader({url: 'https://evening-anchorage-3159.herokuapp.com/api/'});

  constructor(
    private restService: RestService,
    public viewContainerRef: ViewContainerRef,
    public dialog: MatDialog,
    private router: Router
  ) {}

  public ngOnInit() {
    this.getProjects();
  }

  public newProject() {

    const project = new Project();

    project._id = undefined;
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

  private getProjects() {
    this.restService.getProjects()
      .subscribe(
        (parameters) => {
          console.log(parameters);
          //TODO
          this.projects = parameters.projects;
        }
      )
  }

  private editProject(project, dialogTitle: string) {

    if (dialogTitle !== "Create Project") {
      dialogTitle = "Edit Project";
    }

    const config = new MatDialogConfig();
    config.viewContainerRef = this.viewContainerRef;

    this.dialogRef = this.dialog.open(DialogNewProjectComponent, config);
    this.dialogRef.componentInstance.project = project;
    this.dialogRef.componentInstance.dialog_title = dialogTitle;

    this.dialogRef.afterClosed().subscribe((result) => {
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

  private addProject(newProject: Project) {
    // If the user already exists, replace it
    const index = this.projects.findIndex(
      (project) => project._id === newProject._id
    );
    if (index !== -1) {
      this.projects.splice(index, 1, newProject);
    } else {
      this.projects.unshift(newProject);
    }
  }

  private removeProject(_ID: string) {
    // If the user already exists, replace it
    const index = this.projects.findIndex((project) => project._id === _ID);
    if (index !== -1) {
      this.projects.splice(index, 1);
    }
  }

  private selectProject(project: any) {
    this.router.navigate(["project-" + project.project_type, project._id]);
  }
}
