import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

import { ProjectMxComponent } from './project-mx/project-mx.component';

const routes: Routes = [
  { path: 'project-mx/:id', component: ProjectMxComponent }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class ProjectsRoutingModule { }
