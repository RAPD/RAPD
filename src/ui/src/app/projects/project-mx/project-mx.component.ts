import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute, ParamMap } from '@angular/router';

import 'rxjs/add/operator/switchMap';
import { Observable } from 'rxjs/Observable';

import { Project } from '../../shared/classes/project';
import { RestService } from '../../shared/services/rest.service';
import { WebsocketService } from '../../shared/services/websocket.service';

@Component({
  selector: 'app-project-mx',
  templateUrl: './project-mx.component.html',
  styleUrls: ['./project-mx.component.css']
})
export class ProjectMxComponent implements OnInit {

  id: string;
  project: Project;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private rest_service: RestService,
    private websocket_service: WebsocketService
  ) { }

  ngOnInit() {
    this.id = this.route.snapshot.paramMap.get('id');
    console.log(this.id);
    this.getProject(this.id);
  }

  getProject(id:string) {
    this.rest_service.getProject(id)
      .subscribe(
        parameters => {
          console.log(parameters);
          if (parameters.success === true) {
            this.project = parameters.project;
          }
        }
      )
  }

}
