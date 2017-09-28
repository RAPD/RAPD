import { Component,
         OnInit } from '@angular/core';
import { FormGroup,
         FormControl } from '@angular/forms';
import { MatDialogRef } from '@angular/material';

import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-changepass-dialog',
  templateUrl: './changepass-dialog.component.html',
  styleUrls: ['./changepass-dialog.component.css']
})
export class ChangepassDialogComponent implements OnInit {

  submitted: boolean = false;
  error_message: String = '';
  changepass_form: FormGroup;

  constructor(private auth_service: AuthService,
              public dialogRef: MatDialogRef<ChangepassDialogComponent>) { }

  ngOnInit() {

    this.changepass_form = new FormGroup({
      password1: new FormControl(),
      password2: new FormControl()
    })
  }

  onSubmit() {

    this.submitted = true;

    this.auth_service.changePass(this.changepass_form.value);

    this.auth_service.changePass(this.changepass_form.value).subscribe(params => {
      console.log('onSubmit >>', params);

      // if (params.success === true) {

      // Close dialog
      this.dialogRef.close(params);
      // } else {
      //   this.error_message = params.message;
      // }
      this.submitted = false;
    });
  }

  exitChangepass() {
    this.dialogRef.close(undefined);
  }

  passMatch() {
    return this.changepass_form.value.password1 === this.changepass_form.value.password2;
  }

}
