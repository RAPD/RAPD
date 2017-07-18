import { Component, Input, OnInit } from '@angular/core';
import { FormGroup, FormControl } from '@angular/forms';

import { MdDialogRef } from '@angular/material';

import { AdminService } from '../../shared/services/admin.service';
import { Group } from '../../shared/classes/group';
import { Session } from '../../shared/classes/session';

@Component({
  selector: 'app-session-dialog',
  templateUrl: './session-dialog.component.html',
  styleUrls: ['./session-dialog.component.css']
})
export class SessionDialogComponent implements OnInit {

  submitted: boolean = false;
  error_message: string;
  @Input() session: Session;
  model: Session;
  @Input() groups: Group[];
  session_form: FormGroup;

  sites = [
    '24-ID-E',
    '24-ID-C'
  ]

  // session_types = [
  //   'mx'
  // ]

  constructor(private admin_service: AdminService,
              public dialogRef: MdDialogRef<SessionDialogComponent>) { }

  ngOnInit() {

    console.log(this.session);

    this.model = Object.assign({}, this.session);

    this.session_form = new FormGroup({
      group: new FormControl(),
      site: new FormControl(),
      data_root_directory: new FormControl(),
      // session_type: new FormControl()
    });
  }

  exitSession() {
    this.dialogRef.close(undefined);
  }

  submitSession() {

    this.submitted = true;

    this.admin_service.submitSession(this.model).subscribe(params => {
      console.log(params);
      this.submitted = false;
      if (params.success === true) {
        this.dialogRef.close(params);
      } else {
        this.error_message = params;
      }
    });
  }

  deleteSession() {

    this.submitted = true;

    // this.admin_service.deleteGroup(this.group._id).subscribe(params => {
    //   console.log(params);
    //   this.submitted = false;
    //   if (params.success === true) {
    //     this.dialogRef.close(params);
    //   } else {
    //     this.error_message = params;
    //   }
    // });
  }
}
