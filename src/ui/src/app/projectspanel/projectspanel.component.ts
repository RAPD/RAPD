import { Component,
         OnInit } from '@angular/core';
import { MatDialog,
         MatToolbarModule } from '@angular/material';

import { RestService } from '../shared/services/rest.service';
import { Project } from '../shared/classes/project';
import { DialogNewProjectComponent } from '../shared/components/dialog-new-project/dialog-new-project.component';

@Component({
  selector: 'app-projectspanel',
  templateUrl: './projectspanel.component.html',
  styleUrls: ['./projectspanel.component.css']
})
export class ProjectspanelComponent implements OnInit {

  projects: Project[];

  constructor(private rest_service: RestService,
              public dialog: MatDialog) { }

  ngOnInit() {
    this.getProjects();
  }

  getProjects() {
    this.rest_service.getProjects()
      .subscribe(
        parameters => {
          console.log(parameters);
          this.projects = parameters;
        }
      )
  }

  openNewProjectDialog() {
    let dialogRef = this.dialog.open(DialogNewProjectComponent);

    dialogRef.afterClosed().subscribe(result => {
      if (result) {
        this.projects.push(result);
      }
    });
  }

}
