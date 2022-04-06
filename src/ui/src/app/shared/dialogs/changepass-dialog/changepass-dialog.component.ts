import { Component,
         OnInit } from '@angular/core';
import { FormGroup,
         FormControl } from '@angular/forms';
import { MatDialogRef } from '@angular/material/dialog';

import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-changepass-dialog',
  templateUrl: './changepass-dialog.component.html',
  styleUrls: ['./changepass-dialog.component.css']
})
export class ChangepassDialogComponent implements OnInit {

  submitted: boolean = false;
  errorMessage: string = '';
  changepassForm: FormGroup = new FormGroup({
    password1: new FormControl(),
    password2: new FormControl(),
  });

  constructor(private authService: AuthService,
              public dialogRef: MatDialogRef<ChangepassDialogComponent>) { }

  ngOnInit() {

    // this.changepassForm = new FormGroup({
    //   password1: new FormControl(),
    //   password2: new FormControl(),
    // })
  }

  onSubmit() {

    this.submitted = true;

    this.authService.changePass(this.changepassForm.value);

    this.authService.changePass(this.changepassForm.value).subscribe(params => {
      console.log('onSubmit >>', params);

      // if (params.success === true) {

      // Close dialog
      this.dialogRef.close(params);
      // } else {
      //   this.errorMessage = params.message;
      // }
      this.submitted = false;
    });
  }

  exitChangepass() {
    this.dialogRef.close(undefined);
  }

  passMatch() {
    return this.changepassForm.value.password1 === this.changepassForm.value.password2;
  }

}
