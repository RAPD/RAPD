import { Component,
         Inject,
         Input,
         OnInit,
         ViewContainerRef } from '@angular/core';
import { FormGroup,
         FormControl } from '@angular/forms';
import { MatDialogRef,
         MAT_DIALOG_DATA } from '@angular/material';

import { Project } from '../../classes/project';
import { RestService } from '../../../shared/services/rest.service';

@Component({
  selector: 'app-dialog-select-project',
  templateUrl: './dialog-select-project.component.html',
  styleUrls: ['./dialog-select-project.component.css']
})
export class DialogSelectProjectComponent implements OnInit {

  public projects: any;
  public submit_error: string;
  public submitted: boolean = false;
  public model: any = {_id:''};
  public project_form: FormGroup;

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

    if (! form_value._id) {
      return false;
    }

    // Add the result to the form_value
    form_value.result = this.data;

    console.log(form_value);

    this.submitted = true;
    this.rest_service.addResultToProject(form_value)
                     .subscribe(
                       parameters => {
                         console.log(parameters);
                         // A problem connecting to REST server
                         // Submitted is over
                         this.submitted = false;
                         
                         if (parameters.success) {
                           this.dialogRef.close(parameters.project);
                         } else {
                           this.submit_error = parameters.message;
                         }
                       });
  }

}
