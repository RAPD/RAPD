import { Component, Input, OnInit } from '@angular/core';
import { FormGroup, FormControl } from '@angular/forms';

import { MatDialogRef } from '@angular/material';

import { RestService } from '../../shared/services/rest.service';
import { User } from '../../shared/classes/user';
import { Group } from '../../shared/classes/group';

@Component({
  selector: 'app-user-dialog',
  templateUrl: './user-dialog.component.html',
  styleUrls: ['./user-dialog.component.css']
})
export class UserDialogComponent implements OnInit {

  submitted: boolean = false;
  submit_error: string;
  @Input() user: User;
  model: User;
  @Input() groups: Group[];
  user_form: FormGroup;

  constructor(private rest_service: RestService,
              public dialogRef: MatDialogRef<UserDialogComponent>) { }

  ngOnInit() {
    // console.log(this.user);
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

  submitUser() {

    this.submitted = true;

    const form_values = this.user_form.value;
    console.log('form_values', form_values);

    this.model.groups = [];

    // Putting groups into the model as [{_id:...}]
    if (form_values.group0) {
      if (form_values.group0.length > 0) {
        this.model.groups.push({_id: form_values.group0});
    }}
    if (form_values.group1) {
      if (form_values.group1.length > 0) {
        this.model.groups.push({_id: form_values.group1});
    }}
    if (form_values.group2) {
      if (form_values.group2.length > 0) {
        this.model.groups.push({_id: form_values.group2});
    }}

    console.log(this.model);

    this.rest_service.submitUser(this.model).subscribe(params => {
      this.submitted = false;
      if (params.success === true) {
        this.dialogRef.close(params);
      } else {
        this.submit_error = params.message;
      }
    });
  }

  deleteUser() {
    // Mark as submitted
    this.submitted = true;

    // Use REST service
    this.rest_service.deleteUser(this.user._id).subscribe(params => {
      // console.log(params);
      this.submitted = false;
      if (params.success === true) {
        this.dialogRef.close(params);
      } else {
        this.submit_error = params.message;
      }
    });
  }
}
