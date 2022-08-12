import { BrowserModule } from "@angular/platform-browser";
import { NgModule } from "@angular/core";
import { CommonModule } from "@angular/common";
import { FormsModule, ReactiveFormsModule } from "@angular/forms";
import { HttpClientModule, HTTP_INTERCEPTORS } from "@angular/common/http";
// import { Http,
//          HttpModule,
//          RequestOptions } from '@angular/http';
import { AppComponent } from "./app.component";
// import { Router } from '@angular/router';

import { FlexLayoutModule } from "@angular/flex-layout";

import { AppRoutingModule, appRoutingProviders } from "./app.routing";
import { BrowserAnimationsModule } from "@angular/platform-browser/animations";
import { RapdMaterialModule } from "./material.module";
import { NgxDatatableModule } from "@swimlane/ngx-datatable";
import { ChartsModule } from "ng2-charts";

import { LoginGuard } from "./shared/guards/login-guard";
import { AuthService } from "./shared/services/auth.service";
import { RestService } from "./shared/services/rest.service";
import { WebsocketService } from "./shared/services/websocket.service";
import { SessionService } from "./shared/services/session.service";
import { RequestsService } from "./shared/services/requests.service";
import { GlobalsService } from "./shared/services/globals.service";
import { Site } from "./site";

// JWT
// import { JwtModule } from "@auth0/angular-jwt";
import { JwtHttpInterceptor } from "./shared/interceptors/auth.interceptor";

// File Uploader
import { FileUploadModule } from "ng2-file-upload";
import { UploadDialogComponent } from "./shared/dialogs/upload-dialog/upload-dialog.component";

// Welcome & Login
import { LoginDialogComponent } from "./maintoolbar/login-dialog/login-dialog.component";
import { MaintoolbarComponent } from "./maintoolbar/maintoolbar.component";
import { PageNotFoundComponent } from "./page-not-found/page-not-found.component";
import { ChangepassDialogComponent } from "./shared/dialogs/changepass-dialog/changepass-dialog.component";
import { WelcomepanelComponent } from "./welcomepanel/welcomepanel.component";

// Dashboard
import { ActivitiesPanelComponent } from "./dashboard/activities-panel/activities-panel.component";
import { DashboardComponent } from "./dashboard/dashboard.component";
import { OverwatchesPanelComponent } from "./dashboard/overwatches-panel/overwatches-panel.component";
import { SummaryPanelComponent } from "./dashboard/summary-panel/summary-panel.component";

// Projects
import { ProjectsModule } from "./projects/projects.module";
import { ProjectspanelComponent } from "./projectspanel/projectspanel.component";

// Sessions
import { SessionDialogComponent } from "./adminpanel/session-dialog/session-dialog.component";
import { MxSessionpanelComponent } from "./mx-sessionpanel/mx-sessionpanel.component";
import { SessionspanelComponent } from "./sessionspanel/sessionspanel.component";

// Sequence
import { SequenceDialogComponent } from "./shared/dialogs/sequence-dialog/sequence-dialog.component";

// MX
import { MxResultContainerComponent } from "./mx-sessionpanel/mx-result-container/mx-result-container.component";
import { MxResultPanelComponent } from "./mx-sessionpanel/mx-result-container/mx-result-panel/mx-result-panel.component";
import { MxResultslistPanelComponent } from "./mx-sessionpanel/mx-result-container/mx-resultslist-panel/mx-resultslist-panel.component";

// MX Result Components
import { AnalysisF068200Component } from "./plugin_components/mx/analysis-f068-2-0-0/analysis-f068-2-0-0.component";
import { Hcmerge4cba100Component } from "./plugin_components/mx/hcmerge4cba100/hcmerge4cba100.component";
import { Index3b34200Component } from "./plugin_components/mx/index-3b34-2-0-0/index-3b34-2-0-0.component";
import { IntegrateBd11200Component } from "./plugin_components/mx/integrate-bd11-2-0-0/integrate-bd11-2-0-0.component";
import { Pdbquery9a2e200Component } from "./plugin_components/mx/pdbquery9a2e200/pdbquery9a2e200.component";
import { ReindexDialogComponent } from "./plugin_components/mx/index-3b34-2-0-0/reindex-dialog/reindex-dialog.component";
import { Mrc33b200Component } from './plugin_components/mx/mrc33b200/mrc33b200.component';

// MX Request Dialogs
import { MergeDialogComponent } from './plugin_components/mx/merge-dialog/merge-dialog.component';
import { MrDialogComponent } from "./plugin_components/mx/mr-dialog/mr-dialog.component";
import { ReintegrateDialogComponent } from "./plugin_components/mx/reintegrate-dialog/reintegrate-dialog.component";
import { SadDialogComponent } from "./plugin_components/mx/sad-dialog/sad-dialog.component";

// Directives
import { Highlight } from "./shared/directives/highlight.directive";

// Shared Components
import { LogCardComponent } from "./shared/components/log-card/log-card.component";
import { DialogSelectProjectComponent } from "./shared/components/dialog-select-project/dialog-select-project.component";
import { DialogNewProjectComponent } from "./shared/components/dialog-new-project/dialog-new-project.component";
import { DialogUglymolComponent } from "./shared/components/dialog-uglymol/dialog-uglymol.component"

import { AdminpanelComponent } from "./adminpanel/adminpanel.component";
import { TaskspanelComponent } from "./taskspanel/taskspanel.component";

import { UnauthorizedpanelComponent } from "./unauthorizedpanel/unauthorizedpanel.component";
import { UserDialogComponent } from "./adminpanel/user-dialog/user-dialog.component";
import { GroupDialogComponent } from "./adminpanel/group-dialog/group-dialog.component";

import { CommunicateDialogComponent } from "./shared/dialogs/communicate-dialog/communicate-dialog.component";
import { HeaderDialogComponent } from "./plugin_components/mx/header-dialog/header-dialog.component";

import { RunDialogComponent } from "./plugin_components/mx/run-dialog/run-dialog.component";
import { MxImageComponent } from "./plugin_components/mx/mx-image/mx-image.component";

import { ErrorDialogComponent } from "./shared/dialogs/error-dialog/error-dialog.component";
import { ConfirmDialogComponent } from "./shared/dialogs/confirm-dialog/confirm-dialog.component";

export function tokenGetter() {
  return localStorage.getItem("access_token");
}

@NgModule({
    declarations: [
        AppComponent,
        //
        MaintoolbarComponent,
        WelcomepanelComponent,
        PageNotFoundComponent,
        DashboardComponent,
        SummaryPanelComponent,
        OverwatchesPanelComponent,
        ActivitiesPanelComponent,
        SessionspanelComponent,
        ProjectspanelComponent,
        AdminpanelComponent,
        SequenceDialogComponent,
        TaskspanelComponent,
        //
        MxSessionpanelComponent,
        MxResultContainerComponent,
        MxResultslistPanelComponent,
        MxResultPanelComponent,
        //
        Highlight,
        UnauthorizedpanelComponent,
        UserDialogComponent,
        GroupDialogComponent,
        SessionDialogComponent,
        LoginDialogComponent,
        ChangepassDialogComponent,
        CommunicateDialogComponent,
        //
        Index3b34200Component,
        IntegrateBd11200Component,
        AnalysisF068200Component,
        Pdbquery9a2e200Component,
        Hcmerge4cba100Component,
        Mrc33b200Component,
        // INSERT POINT FOR PLUGIN COMPONENTS DECLARATION
        //
        HeaderDialogComponent,
        MxImageComponent,
        ReindexDialogComponent,
        ReintegrateDialogComponent,
        MergeDialogComponent,
        MrDialogComponent,
        SadDialogComponent,
        //
        LogCardComponent,
        RunDialogComponent,
        DialogSelectProjectComponent,
        DialogNewProjectComponent,
        DialogUglymolComponent,
        ErrorDialogComponent,
        ConfirmDialogComponent,
        UploadDialogComponent,
        Hcmerge4cba100Component,
    ],
    imports: [
        BrowserModule,
        CommonModule,
        FormsModule,
        ReactiveFormsModule,
        HttpClientModule,
        // JwtModule.forRoot({
        //   config: {
        //     tokenGetter: tokenGetter,
        //     whitelistedDomains: [/^null$/], //  ['localhost:3000'], // new Array(new RegExp('^null$')),
        //     // blacklistedRoutes: ['localhost:3001/auth/']
        //   }
        // }),
        BrowserAnimationsModule,
        RapdMaterialModule,
        FlexLayoutModule,
        NgxDatatableModule,
        ChartsModule,
        ProjectsModule,
        AppRoutingModule,
        FileUploadModule
    ],
    providers: [
        appRoutingProviders,
        LoginGuard,
        AuthService,
        RestService,
        WebsocketService,
        SessionService,
        RequestsService,
        GlobalsService,
        Site,
        // Replacement for AUTH_PROVIDERS
        { provide: HTTP_INTERCEPTORS, useClass: JwtHttpInterceptor, multi: true }
    ],
    bootstrap: [AppComponent]
})
export class AppModule {}
