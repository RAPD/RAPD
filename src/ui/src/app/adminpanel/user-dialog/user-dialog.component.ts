import { Component, Input, OnInit } from '@angular/core';
import { FormGroup, FormControl } from '@angular/forms';

import { MdDialogRef } from '@angular/material';

import { AdminService } from '../../shared/services/admin.service';
import { User } from '../../shared/classes/user';
import { Group } from '../../shared/classes/group';

@Component({
  selector: 'app-user-dialog',
  templateUrl: './user-dialog.component.html',
  styleUrls: ['./user-dialog.component.css']
})
export class UserDialogComponent implements OnInit {

  submitted: boolean = false;
  error_message: string;
  @Input() user: User;
  model: User;
  @Input() groups: Group[];
  user_form: FormGroup;

  constructor(private admin_service: AdminService,
              public dialogRef: MdDialogRef<UserDialogComponent>) { }

  ngOnInit() {

    console.log(this.user);

    this.model = Object.assign({}, this.user);

    this.user_form = new FormGroup({
      email: new FormControl(),
      username: new FormControl(),
      role: new FormControl(),
      group0: new FormControl(),
      group1: new FormControl(),
      group2: new FormControl()
    });

  }

  exitUser() {

    // Make sure the group names match the group _id
    for (let g of this.user.groups) {
      if (g._id === '') {
        let index = this.user.groups.indexOf(g);
        this.user.groups.slice(index, 1);
      }
    }

    this.dialogRef.close(undefined);

    // console.log(this.user.groups);
  }

  submitUser() {

    this.submitted = true;

    let form_values = this.user_form.value;

    console.log('form_values', form_values);

    // this.model.groups = [];

    if (form_values.group0) {
      this.model.groups.push({_id: form_values.group0});
    }
    if (form_values.group1) {
      this.model.groups.push({_id: form_values.group1});
    }
    if (form_values.group2) {
      this.model.groups.push({_id: form_values.group2});
    }

    // Make sure the group names match the group _id
    for (let g of this.model.groups) {
      let filtered = this.groups.filter(group => group._id === g._id);
      console.log('Filtered:', filtered);
      g.groupname = filtered[0].groupname;
    }

    this.admin_service.submitUser(this.model).subscribe(params => {
      console.log(params);
      this.submitted = false;
      if (params.success === true) {
        this.dialogRef.close(params);
      } else {
        this.error_message = params;
      }
    });
  }

  deleteUser() {

    this.submitted = true;

    this.admin_service.deleteUser(this.user._id).subscribe(params => {
      console.log(params);
      this.submitted = false;
      if (params.success === true) {
        this.dialogRef.close(params);
      } else {
        this.error_message = params;
      }
    });
  }
}
