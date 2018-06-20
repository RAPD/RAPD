import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { RapdMaterialModule } from '../material.module';
import { FlexLayoutModule } from '@angular/flex-layout';

import { FileUploadModule } from 'ng2-file-upload';

import { ProjectMxComponent } from './project-mx/project-mx.component';

import { ProjectsRoutingModule } from './projects-routing.module';

@NgModule({
  imports: [
    CommonModule,
    RapdMaterialModule,
    FileUploadModule,
    FlexLayoutModule,
    ProjectsRoutingModule
  ],
  declarations: [
    ProjectMxComponent
  ]
})
export class ProjectsModule { }
