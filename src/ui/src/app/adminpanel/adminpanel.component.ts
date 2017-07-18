import { Component,
         OnInit,
         ViewContainerRef } from '@angular/core';

import { MdDialogRef,
         MdDialog,
         MdDialogConfig } from '@angular/material';

import { UserDialogComponent } from './user-dialog/user-dialog.component';
import { GroupDialogComponent } from './group-dialog/group-dialog.component';
import { SessionDialogComponent } from './session-dialog/session-dialog.component';
import { ChangepassDialogComponent } from '../shared/dialogs/changepass-dialog/changepass-dialog.component';


import { AdminService } from '../shared/services/admin.service';
import { User } from '../shared/classes/user';
import { Group } from '../shared/classes/group';
import { Session } from '../shared/classes/session';

@Component({
  selector: 'app-adminpanel',
  templateUrl: './adminpanel.component.html',
  styleUrls: ['./adminpanel.component.css']
})
export class AdminpanelComponent implements OnInit {

  userDialogRef: MdDialogRef<UserDialogComponent>;
  changepassDialogRef: MdDialogRef<ChangepassDialogComponent>;
  groupDialogRef: MdDialogRef<GroupDialogComponent>;
  sessionDialogRef: MdDialogRef<SessionDialogComponent>;

  user: User;
  users: User[];
  groups: Group[];
  user_groups: Group[] = [];
  sessions: Session[];
  errorMessage: string;

  constructor(private admin_service: AdminService,
              public dialog: MdDialog,
              public viewContainerRef: ViewContainerRef) { }

  ngOnInit() {

    var self = this;

    this.getUsers();
    this.getGroups();
    this.getSessions();

    // Get the user profile
    this.user = JSON.parse(localStorage.getItem('profile'));
    console.log(this.user);

  }

  getUsers() {
    this.admin_service.getUsers()
      .subscribe(
       users => this.users = users,
       error => this.errorMessage = <any>error);
  }

  getGroups() {

    var self = this;

    this.admin_service.getGroups()
      .subscribe(
       groups => this.groups = groups,
       error => this.errorMessage = <any>error,
       function() {
         // Assemble the user's groups into a list
         for (let group_id of self.user.groups) {
           console.log('group_id', group_id);
           let index = self.groups.findIndex(group => group._id === group_id);
           self.user_groups.push(self.groups[index]);
         }
       }
     );
  }

  getSessions() {
    this.admin_service.getSessions()
      .subscribe(
       sessions => this.sessions = sessions,
       error => this.errorMessage = <any>error);
  }

  // New user button is clicked
  newUser() {
    let user = new User();

    user._id = undefined;
    user.email = undefined;
    user.username = undefined;
    user.groups = [];
    user.loginAttempts = 0;
    user.role = 'user';
    user.status = 'active';

    let pseudo_event = {
      selected: [user]
    };

    this.editUser(pseudo_event);
  }

  // A user entry is clicked on
  editUser(event) {

    let user = event.selected[0];

    let config = new MdDialogConfig();
    config.viewContainerRef = this.viewContainerRef;

    this.userDialogRef = this.dialog.open(UserDialogComponent, config);
    this.userDialogRef.componentInstance.user = user;
    this.userDialogRef.componentInstance.groups = this.groups;

    this.userDialogRef.afterClosed().subscribe(result => {
      // console.log('closed', result);
      this.userDialogRef = null;
      if (result !== undefined) {
        if (result.operation === 'delete') {
          this.deleteUser(result._id);
        } if (result.operation === 'add') {
          this.addUser(result.user);
        } if (result.operation === 'edit') {
          this.addUser(result.user);
        }
      }
    });
  }

  changePass() {
    let config = new MdDialogConfig();
    config.viewContainerRef = this.viewContainerRef;
    this.changepassDialogRef = this.dialog.open(ChangepassDialogComponent, config);
  }

  addUser(new_user: User) {
    console.log('addUser:', new_user);
    // If the user already exists, replace it
    let index = this.users.findIndex(user => user._id === new_user._id);
    if (index !== -1) {
      this.users.splice(index, 1, new_user);
    } else {
      this.users.unshift(new_user);
    }
  }

  deleteUser(_id: string) {
    console.log('deleteUser', _id);
    // If the user already exists, replace it
    let index = this.users.findIndex(user => user._id === _id);
    if (index !== -1) {
      this.users.splice(index, 1);
    }
  }

  // Create a new group
  createGroup() {
    let pseudo_event = {
      selected: [undefined]
    };

    this.editGroup(pseudo_event);
  }

  // A group entry is clicked on
  editGroup(event) {

    let group = event.selected[0];

    console.log(group);

    if (group === undefined) {
      group = new Group();
      group._id = undefined;
      group.groupname = undefined;
      group.institution = undefined;
      group.uid = undefined;
      group.gid = undefined;
      group.status = 'active';
    }

    let config = new MdDialogConfig();
    config.viewContainerRef = this.viewContainerRef;

    this.groupDialogRef = this.dialog.open(GroupDialogComponent, config);
    this.groupDialogRef.componentInstance.group = group;

    this.groupDialogRef.afterClosed().subscribe(result => {
      console.log('closed', result);
      this.groupDialogRef = null;
      if (result !== undefined) {
        if (result.operation === 'delete') {
          this.deleteGroup(result._id);
        } if (result.operation === 'add') {
          this.addGroup(result.group);
        } if (result.operation === 'edit') {
          this.addGroup(result.group);
        }
      }
    });
  }

  addGroup(new_group: Group) {
    console.log('addGroup:', new_group);
    // If the user already exists, replace it
    let index = this.groups.findIndex(group => group._id === new_group._id);
    if (index !== -1) {
      this.groups.splice(index, 1, new_group);
    } else {
      this.groups.unshift(new_group);
    }
  }

  deleteGroup(_id: string) {
    console.log('deleteGroup', _id);
    // If the user already exists, replace it
    let index = this.groups.findIndex(group => group._id === _id);
    if (index !== -1) {
      this.groups.splice(index, 1);
    }
  }

  // Ctreate a new session
  createSession() {

    // Create a pseudo-event for the editSession method
    let pseudo_event = {
      selected: [undefined]
    };

    // Call the editSession method
    this.editSession(pseudo_event);
  }

  // A session entry is clicked on
  editSession(event) {

    let session = event.selected[0];

    // console.log(session);

    if (session === undefined) {
      session = new Session();
      session._id = undefined;
      session.group = {
        _id: undefined,
        groupname: undefined
      };
      session.site = undefined;
      session.session_type = 'mx';
    }

    let config = new MdDialogConfig();
    config.viewContainerRef = this.viewContainerRef;

    this.sessionDialogRef = this.dialog.open(SessionDialogComponent, config);
    this.sessionDialogRef.componentInstance.session = session;
    this.sessionDialogRef.componentInstance.groups = this.groups;

    this.sessionDialogRef.afterClosed().subscribe(result => {
      // console.log('closed', result);
      this.sessionDialogRef = null;
      if (result !== undefined) {
        if (result.operation === 'delete') {
          this.deleteSession(result._id);
        } if (result.operation === 'add') {
          this.addSession(result.session);
        } if (result.operation === 'edit') {
          this.addSession(result.session);
        }
      }
    });
  }

  addSession(new_session: Session) {
    console.log('addSession:', new_session);
    // If the session already exists, replace it
    let index = this.sessions.findIndex(session => session._id === new_session._id);
    if (index !== -1) {
      this.sessions.splice(index, 1, new_session);
    } else {
      this.sessions.unshift(new_session);
    }
  }

  deleteSession(_id: string) {
    console.log('deleteSession', _id);
    // If the session already exists, replace it
    let index = this.sessions.findIndex(session => session._id === _id);
    if (index !== -1) {
      this.sessions.splice(index, 1);
    }
  }
}
