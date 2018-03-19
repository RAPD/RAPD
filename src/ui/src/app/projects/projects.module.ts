import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { RapdMaterialModule } from '../rapd.module';
import { FlexLayoutModule } from '@angular/flex-layout';

import { ProjectMxComponent } from './project-mx/project-mx.component';

import { ProjectsRoutingModule } from './projects-routing.module';

@NgModule({
  imports: [
    CommonModule,
    RapdMaterialModule,
    FlexLayoutModule,
    ProjectsRoutingModule
  ],
  declarations: [
    ProjectMxComponent
  ]
})
export class ProjectsModule { }
