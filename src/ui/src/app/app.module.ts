import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { HttpModule, Http, RequestOptions } from '@angular/http';
import { AppComponent } from './app.component';
import { Router } from '@angular/router';

import { AppRoutingModule,
         appRoutingProviders } from './app.routing';

import 'hammerjs';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { MaterialModule } from '@angular/material';
import { NgxDatatableModule } from '@swimlane/ngx-datatable';

import { LoginGuard } from './shared/guards/login-guard';
import { AuthService } from './shared/services/auth.service';
import { AdminService } from './shared/services/admin.service';
import { ResultsService } from './shared/services/results.service';
import { SessionService } from './shared/services/session.service';
import { provideAuth, AuthHttp, AuthConfig } from 'angular2-jwt';

import { MaintoolbarComponent } from './maintoolbar/maintoolbar.component';
import { WelcomepanelComponent } from './welcomepanel/welcomepanel.component';
import { DashboardComponent } from './dashboard/dashboard.component';
import { SessionspanelComponent } from './sessionspanel/sessionspanel.component';
import { ProjectspanelComponent } from './projectspanel/projectspanel.component';
import { AdminpanelComponent } from './adminpanel/adminpanel.component';
import { TaskspanelComponent } from './taskspanel/taskspanel.component';
import { MxSessionpanelComponent } from './mx-sessionpanel/mx-sessionpanel.component';
import { MxResultContainerComponent } from './mx-sessionpanel/mx-result-container/mx-result-container.component';
import { MxResultslistPanelComponent } from './mx-sessionpanel/mx-result-container/mx-resultslist-panel/mx-resultslist-panel.component';
import { MxResultPanelComponent } from './mx-sessionpanel/mx-result-container/mx-result-panel/mx-result-panel.component';
import { IndexstrategyAaaa1Component } from './agent_components/mx/indexstrategy-aaaa-1/indexstrategy-aaaa-1.component';
import { Highlight } from './shared/directives/highlight.directive';
// import { LoginComponent } from './login/login.component';
import { LoginPanelComponent } from './login-panel/login-panel.component';
import { UnauthorizedpanelComponent } from './unauthorizedpanel/unauthorizedpanel.component';
import { UserDialogComponent } from './adminpanel/user-dialog/user-dialog.component';
import { GroupDialogComponent } from './adminpanel/group-dialog/group-dialog.component';
import { SessionDialogComponent } from './adminpanel/session-dialog/session-dialog.component';
import { LoginDialogComponent } from './maintoolbar/login-dialog/login-dialog.component';
import { ChangepassDialogComponent } from './shared/dialogs/changepass-dialog/changepass-dialog.component';
import { CommunicateDialogComponent } from './shared/dialogs/communicate-dialog/communicate-dialog.component';

export function authHttpServiceFactory(http: Http, options: RequestOptions) {
  return new AuthHttp( new AuthConfig({}), http, options);
}

@NgModule({
  declarations: [
    AppComponent,
    MaintoolbarComponent,
    WelcomepanelComponent,
    DashboardComponent,
    SessionspanelComponent,
    ProjectspanelComponent,
    AdminpanelComponent,
    TaskspanelComponent,
    MxSessionpanelComponent,
    MxResultContainerComponent,
    MxResultslistPanelComponent,
    MxResultPanelComponent,
    IndexstrategyAaaa1Component,
    Highlight,
    // LoginComponent,
    LoginPanelComponent,
    UnauthorizedpanelComponent,
    UserDialogComponent,
    GroupDialogComponent,
    SessionDialogComponent,
    LoginDialogComponent,
    ChangepassDialogComponent,
    CommunicateDialogComponent
  ],
  imports: [
    NgxDatatableModule,
    BrowserModule,
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    AppRoutingModule,
    HttpModule,
    BrowserAnimationsModule,
    MaterialModule
  ],
  providers: [ appRoutingProviders,
               LoginGuard,
               AuthService,
               AdminService,
               ResultsService,
               SessionService,
               // Replacement for AUTH_PROVIDERS
               {
                 provide: AuthHttp,
                 useFactory: authHttpServiceFactory,
                 deps: [ Http, RequestOptions ]
               } ],
              //  provideAuth({
              //   tokenName: 'token'
              //  }),
              // HTTP_PROVIDERS ],
  entryComponents: [
    AppComponent,
    UserDialogComponent,
    GroupDialogComponent,
    SessionDialogComponent,
    LoginDialogComponent,
    ChangepassDialogComponent
  ],
  bootstrap: [AppComponent]
})
export class AppModule {

}