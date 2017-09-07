import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { HttpModule, Http, RequestOptions } from '@angular/http';
import { AppComponent } from './app.component';
import { Router } from '@angular/router';

import { FlexLayoutModule } from '@angular/flex-layout';

import { AppRoutingModule,
         appRoutingProviders } from './app.routing';

import 'hammerjs';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { MaterialModule,
         MdDialogModule } from '@angular/material';
import { NgxDatatableModule } from '@swimlane/ngx-datatable';
import { ChartsModule } from 'ng2-charts/ng2-charts';

import { LoginGuard } from './shared/guards/login-guard';
import { AuthService } from './shared/services/auth.service';
import { AdminService } from './shared/services/admin.service';
import { ResultsService } from './shared/services/results.service';
import { SessionService } from './shared/services/session.service';
import { RequestsService } from './shared/services/requests.service';
import { GlobalsService } from './shared/services/globals.service';
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
import { Highlight } from './shared/directives/highlight.directive';
import { LoginPanelComponent } from './login-panel/login-panel.component';
import { UnauthorizedpanelComponent } from './unauthorizedpanel/unauthorizedpanel.component';
import { UserDialogComponent } from './adminpanel/user-dialog/user-dialog.component';
import { GroupDialogComponent } from './adminpanel/group-dialog/group-dialog.component';
import { SessionDialogComponent } from './adminpanel/session-dialog/session-dialog.component';
import { LoginDialogComponent } from './maintoolbar/login-dialog/login-dialog.component';
import { ChangepassDialogComponent } from './shared/dialogs/changepass-dialog/changepass-dialog.component';
import { CommunicateDialogComponent } from './shared/dialogs/communicate-dialog/communicate-dialog.component';

import { IndexstrategyAaaa1Component } from './plugin_components/mx/indexstrategy-aaaa-1/indexstrategy-aaaa-1.component';
import { Index3b34200Component } from './plugin_components/mx/index-3b34-2-0-0/index-3b34-2-0-0.component';
import { PlotOmegaStartComponent } from './plugin_components/mx/index-3b34-2-0-0/plot-omega-start/plot-omega-start.component';
import { ReindexDialogComponent } from './plugin_components/mx/index-3b34-2-0-0/reindex-dialog/reindex-dialog.component';
import { HeaderDialogComponent } from './plugin_components/mx/header-dialog/header-dialog.component';
import { IntegrateBd11200Component } from './plugin_components/mx/integrate-bd11-2-0-0/integrate-bd11-2-0-0.component';
import { AnalysisF068200Component } from './plugin_components/mx/analysis-f068-2-0-0/analysis-f068-2-0-0.component';

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
    Highlight,
    LoginPanelComponent,
    UnauthorizedpanelComponent,
    UserDialogComponent,
    GroupDialogComponent,
    SessionDialogComponent,
    LoginDialogComponent,
    ChangepassDialogComponent,
    CommunicateDialogComponent,
    IndexstrategyAaaa1Component,
    Index3b34200Component,
    PlotOmegaStartComponent,
    HeaderDialogComponent,
    ReindexDialogComponent,
    IntegrateBd11200Component,
    AnalysisF068200Component
  ],
  imports: [
    BrowserModule,
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    AppRoutingModule,
    HttpModule,
    BrowserAnimationsModule,
    FlexLayoutModule,
    MaterialModule,
    MdDialogModule,
    NgxDatatableModule,
    ChartsModule
  ],
  providers: [ appRoutingProviders,
               LoginGuard,
               AuthService,
               AdminService,
               ResultsService,
               SessionService,
               RequestsService,
               GlobalsService,
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
    ChangepassDialogComponent,
    PlotOmegaStartComponent,
    HeaderDialogComponent,
    ReindexDialogComponent
  ],
  bootstrap: [AppComponent]
})
export class AppModule {

}
