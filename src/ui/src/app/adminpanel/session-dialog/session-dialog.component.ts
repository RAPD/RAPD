import { Component, Input, OnInit } from '@angular/core';
import { FormGroup, FormControl } from '@angular/forms';

import { MatDialogRef } from '@angular/material';

import { GlobalsService } from '../../shared/services/globals.service';
import { RestService } from '../../shared/services/rest.service';
import { Group } from '../../shared/classes/group';
import { Session } from '../../shared/classes/session';

@Component({
  selector: 'app-session-dialog',
  templateUrl: './session-dialog.component.html',
  styleUrls: ['./session-dialog.component.css']
})
export class SessionDialogComponent implements OnInit {

  submitted: boolean = false;
  submit_error: string;
  @Input() session: Session;
  model: Session;
  @Input() groups: Group[];
  session_form: FormGroup;

  constructor(private globals_service: GlobalsService,
              private admin_service: RestService,
              public dialogRef: MatDialogRef<SessionDialogComponent>) { }

  ngOnInit() {

    console.log(this.session);

    console.log(this.globals_service.site.site_tags);

    this.model = Object.assign({}, this.session);
    if (this.model.group === null) {
      this.model.group = {_id:''};
    }
    this.session_form = new FormGroup({
      group: new FormControl(),
      site: new FormControl(),
      data_root_dir: new FormControl(),
      // session_type: new FormControl()
    });
  }

  exitSession() {
    this.dialogRef.close(undefined);
  }

  submitSession() {

    this.submitted = true;

    this.admin_service.submitSession(this.model).subscribe(params => {
      this.submitted = false;
      if (params.success === true) {
        this.dialogRef.close(params);
      } else {
        this.submit_error = params.message;
      }
    });
  }

  deleteSession() {

    this.submitted = true;

    this.admin_service.deleteSession(this.session._id).subscribe(params => {
      console.log(params);
      this.submitted = false;
      if (params.success === true) {
        this.dialogRef.close(params);
      } else {
        this.submit_error = params.message;
      }
    });
  }
}
