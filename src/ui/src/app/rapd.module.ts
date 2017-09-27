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
         MatToolbarModule,
         MatSnackBarModule, } from '@angular/material';

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
    MatSnackBarModule,
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
    MatSnackBarModule, 
  ]
})
export class RapdMaterialModule { }
