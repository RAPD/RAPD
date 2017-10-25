import { NgModule } from '@angular/core';
import { Routes, RouterModule }   from '@angular/router';

import { LoginGuard } from './shared/guards/login-guard';

// import { LoginPanelComponent } from './login-panel/login-panel.component';
import { WelcomepanelComponent } from './welcomepanel';
import { DashboardComponent } from './dashboard';
import { SessionspanelComponent } from './sessionspanel';
import { ProjectspanelComponent } from './projectspanel';
import { TaskspanelComponent } from './taskspanel';
import { AdminpanelComponent } from './adminpanel';
import { UnauthorizedpanelComponent } from './unauthorizedpanel/unauthorizedpanel.component';
import { MxSessionpanelComponent } from './mx-sessionpanel';

const appRoutes: Routes = [
  { path: '',
      component: WelcomepanelComponent },
  { path: 'dashboard',
      component: DashboardComponent },
  { path: 'sessions',
    component: SessionspanelComponent,
    canActivate: [ LoginGuard ]},
  { path: 'projects',
      component: ProjectspanelComponent,
      canActivate: [ LoginGuard ]},
  { path: 'tasks',
      component: TaskspanelComponent,
      canActivate: [ LoginGuard ]},
  { path: 'admin',
      component: AdminpanelComponent,
      canActivate: [ LoginGuard ]},
  { path: 'mx/:session_id',
      component: MxSessionpanelComponent,
      canActivate: [ LoginGuard ],
      children: []},
  // { path: 'login',
  //     component: LoginPanelComponent },
  { path: 'unauthorized',
      component: UnauthorizedpanelComponent}
  // { path: '**', component: PageNotFoundComponent }
];

export const appRoutingProviders: any[] = [

];

// export const routing = RouterModule.forRoot(appRoutes);

@NgModule({
imports: [ RouterModule.forRoot(appRoutes) ],
exports: [ RouterModule ]
})
export class AppRoutingModule {}
