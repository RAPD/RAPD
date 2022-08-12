import { Component, Input, OnInit } from '@angular/core';
import { UntypedFormGroup,
         UntypedFormControl } from '@angular/forms';

import { MatDialogRef } from '@angular/material/dialog';

import { GlobalsService } from '../../shared/services/globals.service';
import { RestService } from '../../shared/services/rest.service';
import { Group } from '../../shared/classes/group';

@Component({
  selector: 'app-group-dialog',
  templateUrl: './group-dialog.component.html',
  styleUrls: ['./group-dialog.component.css']
})
export class GroupDialogComponent implements OnInit {

  submitted: boolean = false;
  error_message: string;
  @Input() group: Group;
  model: Group;
  group_form: UntypedFormGroup;

  constructor(private admin_service: RestService,
              public globals_service: GlobalsService,
              public dialogRef: MatDialogRef<GroupDialogComponent>) { }

  ngOnInit() {

    console.log(this.group);

    this.model = Object.assign({}, this.group);

    this.group_form = new UntypedFormGroup({
      groupname: new UntypedFormControl(),
      institution: new UntypedFormControl(),
      role: new UntypedFormControl(),
      uid: new UntypedFormControl(),
      uidNumber: new UntypedFormControl(),
      gidNumber: new UntypedFormControl(),
      status: new UntypedFormControl()
    });
  }

  exitGroup() {
    this.dialogRef.close(undefined);
  }

  submitGroup() {

    this.submitted = true;

    this.admin_service.submitGroup(this.model).subscribe(params => {
      console.log(params);
      this.submitted = false;
      if (params.success === true) {
        this.dialogRef.close(params);
      } else {
        this.error_message = params;
      }
    });
  }

  deleteGroup() {

    this.submitted = true;

    this.admin_service.deleteGroup(this.group._id).subscribe(params => {
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
