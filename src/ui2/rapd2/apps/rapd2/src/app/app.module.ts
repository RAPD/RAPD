import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { RouterModule } from '@angular/router';

import { AppComponent } from './app.component';
import { NxWelcomeComponent } from './nx-welcome.component';
import { LandingComponent } from './landing/landing.component';
import { MaintoolbarComponent } from './maintoolbar/maintoolbar.component';

@NgModule({
  declarations: [
    AppComponent,
    NxWelcomeComponent,
    LandingComponent,
    MaintoolbarComponent,
  ],
  imports: [
    BrowserModule,
    RouterModule.forRoot([
      {
        path: '',
        pathMatch: 'full',
        redirectTo: '/landing',
      },
      {
        path: 'landing',
        component: LandingComponent,
      },
    ]),
  ],
  providers: [],
  bootstrap: [AppComponent],
})
export class AppModule {}
