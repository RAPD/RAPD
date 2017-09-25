import { NgModule } from '@angular/core';

import { MatButtonModule,
         MatCardModule,
         MatDialogModule,
         MatIconModule,
         MatInputModule,
         MatListModule,
         MatProgressSpinnerModule,
         MatSelectModule,
         MatTabsModule,
         MatToolbarModule, } from '@angular/material';

@NgModule({
  imports: [
    MatButtonModule,
    MatCardModule,
    MatDialogModule,
    MatIconModule,
    MatInputModule,
    MatListModule,
    MatProgressSpinnerModule,
    MatSelectModule,
    MatTabsModule,
    MatToolbarModule,
  ],
  exports: [
    MatButtonModule,
    MatCardModule,
    MatDialogModule,
    MatIconModule,
    MatInputModule,
    MatListModule,
    MatProgressSpinnerModule,
    MatSelectModule,
    MatTabsModule,
    MatToolbarModule,
  ]
})
export class RapdMaterialModule { }
