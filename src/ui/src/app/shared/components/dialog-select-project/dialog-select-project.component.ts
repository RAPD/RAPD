import { Component,
         Inject,
         Input,
         OnInit } from '@angular/core';
import { FormGroup,
         FormControl } from '@angular/forms';
import { MatDialogRef,
         MAT_DIALOG_DATA } from '@angular/material';

import { RestService } from '../../../shared/services/rest.service';

@Component({
  selector: 'app-dialog-select-project',
  templateUrl: './dialog-select-project.component.html',
  styleUrls: ['./dialog-select-project.component.css']
})
export class DialogSelectProjectComponent implements OnInit {

  private projects: any;
  private submit_error: string;
  private submitted: boolean = false;
  private model: any = {_id:''};
  private project_form: FormGroup;

  constructor(@Inject(MAT_DIALOG_DATA) public data: any,
              public dialogRef: MatDialogRef<DialogSelectProjectComponent>,
              private rest_service: RestService) { }

  ngOnInit() {

    // Get available projects
    this.rest_service.getProjects().subscribe(
      parameters => {
        console.log(parameters);
        this.projects = parameters;
      }
    )

    // Create the form group
    this.project_form = new FormGroup({
      _id: new FormControl(),
    });
  }

  submitProjectSelection() {
    let form_value = this.project_form.value;

    console.log(form_value);

    if (! form_value._id) {
      return false;
    }

    // Add the result to the form_value
    form_value.result = this.data;

    this.submitted = true;
    this.rest_service.addResultToProject(form_value)
                     .subscribe(
                       parameters => {
                         console.log(parameters);
                         // A problem connecting to REST server
                         // Submitted is over
                         this.submitted = false;
                         this.submit_error = parameters.error;
                         if (parameters.success) {
                           this.dialogRef.close(parameters.project);
                         }
                       });
  }

}
