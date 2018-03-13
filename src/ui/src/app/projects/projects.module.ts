import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { ProjectMxComponent } from './project-mx/project-mx.component';

import { ProjectsRoutingModule } from './projects-routing.module';

@NgModule({
  imports: [
    CommonModule,
    ProjectsRoutingModule
  ],
  declarations: [
    ProjectMxComponent
  ]
})
export class ProjectsModule { }
