import { Component, OnInit } from '@angular/core';

import { RestService } from '../shared/services/rest.service';
import { Project } from '../shared/classes/project';

@Component({
  selector: 'app-projectspanel',
  templateUrl: './projectspanel.component.html',
  styleUrls: ['./projectspanel.component.css']
})
export class ProjectspanelComponent implements OnInit {

  projects: Project[];

  constructor(private rest_service: RestService) { }

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

}
