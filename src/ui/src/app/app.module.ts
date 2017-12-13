import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule,
         ReactiveFormsModule } from '@angular/forms';
// import { HttpClientModule } from '@angular/common/http';
import { Http,
         HttpModule,
         RequestOptions } from '@angular/http';
import { AppComponent } from './app.component';
import { Router } from '@angular/router';

import { FlexLayoutModule } from '@angular/flex-layout';

import { AppRoutingModule,
         appRoutingProviders } from './app.routing';

import 'hammerjs';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { RapdMaterialModule } from './rapd.module';
import { NgxDatatableModule } from '@swimlane/ngx-datatable';
import { ChartsModule } from 'ng2-charts/ng2-charts';

import { LoginGuard } from './shared/guards/login-guard';
import { AuthService } from './shared/services/auth.service';
import { RestService } from './shared/services/rest.service';
import { WebsocketService } from './shared/services/websocket.service';
import { SessionService } from './shared/services/session.service';
import { RequestsService } from './shared/services/requests.service';
import { GlobalsService } from './shared/services/globals.service';
import { Site } from './site';
import { provideAuth, AuthHttp, AuthConfig } from 'angular2-jwt';

import { MaintoolbarComponent } from './maintoolbar/maintoolbar.component';
import { WelcomepanelComponent } from './welcomepanel/welcomepanel.component';

import { DashboardComponent } from './dashboard/dashboard.component';
import { SummaryPanelComponent } from './dashboard/summary-panel/summary-panel.component';
import { OverwatchesPanelComponent } from './dashboard/overwatches-panel/overwatches-panel.component';
import { ActivitiesPanelComponent } from './dashboard/activities-panel/activities-panel.component';

import { SessionspanelComponent } from './sessionspanel/sessionspanel.component';
import { ProjectspanelComponent } from './projectspanel/projectspanel.component';
import { AdminpanelComponent } from './adminpanel/adminpanel.component';
import { TaskspanelComponent } from './taskspanel/taskspanel.component';
import { MxSessionpanelComponent } from './mx-sessionpanel/mx-sessionpanel.component';
import { MxResultContainerComponent } from './mx-sessionpanel/mx-result-container/mx-result-container.component';
import { MxResultslistPanelComponent } from './mx-sessionpanel/mx-result-container/mx-resultslist-panel/mx-resultslist-panel.component';
import { MxResultPanelComponent } from './mx-sessionpanel/mx-result-container/mx-result-panel/mx-result-panel.component';
import { Highlight } from './shared/directives/highlight.directive';
import { UnauthorizedpanelComponent } from './unauthorizedpanel/unauthorizedpanel.component';
import { UserDialogComponent } from './adminpanel/user-dialog/user-dialog.component';
import { GroupDialogComponent } from './adminpanel/group-dialog/group-dialog.component';
import { SessionDialogComponent } from './adminpanel/session-dialog/session-dialog.component';
import { LoginDialogComponent } from './maintoolbar/login-dialog/login-dialog.component';
import { ChangepassDialogComponent } from './shared/dialogs/changepass-dialog/changepass-dialog.component';
import { CommunicateDialogComponent } from './shared/dialogs/communicate-dialog/communicate-dialog.component';

import { Index3b34200Component } from './plugin_components/mx/index-3b34-2-0-0/index-3b34-2-0-0.component';
import { ReindexDialogComponent } from './plugin_components/mx/index-3b34-2-0-0/reindex-dialog/reindex-dialog.component';
import { HeaderDialogComponent } from './plugin_components/mx/header-dialog/header-dialog.component';
import { IntegrateBd11200Component } from './plugin_components/mx/integrate-bd11-2-0-0/integrate-bd11-2-0-0.component';
import { AnalysisF068200Component } from './plugin_components/mx/analysis-f068-2-0-0/analysis-f068-2-0-0.component';
import { LogCardComponent } from './shared/components/log-card/log-card.component';
import { RunDialogComponent } from './plugin_components/mx/run-dialog/run-dialog.component';
import { MxImageComponent } from './plugin_components/mx/mx-image/mx-image.component';
import { ReintegrateDialogComponent } from './plugin_components/mx/reintegrate-dialog/reintegrate-dialog.component';
import { DialogSelectProjectComponent } from './shared/components/dialog-select-project/dialog-select-project.component';
import { DialogNewProjectComponent } from './shared/components/dialog-new-project/dialog-new-project.component';
import { DialogErrorComponent } from './shared/components/dialog-error/dialog-error.component';

export function authHttpServiceFactory(http: Http, options: RequestOptions) {
  return new AuthHttp( new AuthConfig({}), http, options);
}

@NgModule({
  declarations: [
    AppComponent,
    MaintoolbarComponent,
    WelcomepanelComponent,
    DashboardComponent,
    SummaryPanelComponent,
    OverwatchesPanelComponent,
    ActivitiesPanelComponent,
    SessionspanelComponent,
    ProjectspanelComponent,
    AdminpanelComponent,
    TaskspanelComponent,
    MxSessionpanelComponent,
    MxResultContainerComponent,
    MxResultslistPanelComponent,
    MxResultPanelComponent,
    Highlight,
    UnauthorizedpanelComponent,
    UserDialogComponent,
    GroupDialogComponent,
    SessionDialogComponent,
    LoginDialogComponent,
    ChangepassDialogComponent,
    CommunicateDialogComponent,
    Index3b34200Component,
    HeaderDialogComponent,
    ReindexDialogComponent,
    IntegrateBd11200Component,
    AnalysisF068200Component,
    LogCardComponent,
    RunDialogComponent,
    MxImageComponent,
    ReintegrateDialogComponent,
    DialogSelectProjectComponent,
    DialogNewProjectComponent,
    DialogErrorComponent
  ],
  imports: [
    BrowserModule,
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    AppRoutingModule,
    HttpModule,
    BrowserAnimationsModule,
    RapdMaterialModule,
    FlexLayoutModule,
    NgxDatatableModule,
    ChartsModule
  ],
  providers: [ appRoutingProviders,
               LoginGuard,
               AuthService,
               RestService,
               WebsocketService,
               SessionService,
               RequestsService,
               GlobalsService,
               Site,
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
    AnalysisF068200Component,
    AppComponent,
    ChangepassDialogComponent,
    DialogNewProjectComponent,
    DialogSelectProjectComponent,
    GroupDialogComponent,
    HeaderDialogComponent,
    Index3b34200Component,
    IntegrateBd11200Component,
    LoginDialogComponent,
    ReindexDialogComponent,
    ReintegrateDialogComponent,
    RunDialogComponent,
    SessionDialogComponent,
    UserDialogComponent,
  ],
  bootstrap: [AppComponent]
})
export class AppModule {

}
