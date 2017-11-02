import { Component,
         Input,
         OnInit } from '@angular/core';

import { FormGroup,
         FormControl } from '@angular/forms';

import { MatDialogRef,
         MAT_DIALOG_DATA } from '@angular/material';

import { Project } from '../../classes/project';
import { User } from '../../classes/user';
import { RestService } from '../../services/rest.service';

@Component({
  selector: 'app-dialog-new-project',
  templateUrl: './dialog-new-project.component.html',
  styleUrls: ['./dialog-new-project.component.css']
})
export class DialogNewProjectComponent implements OnInit {

  public user: User;
  public profile: any;
  public submit_error:string;
  public submitted:boolean = false;
  @Input() project: Project;
  public model: Project;
  public project_form: FormGroup;

  constructor(private rest_service: RestService,
              public dialogRef: MatDialogRef<DialogNewProjectComponent>) { }

  ngOnInit() {
    // Get the user profile
    this.user = JSON.parse(localStorage.getItem('profile'));

    // Load the model with project
    this.model = Object.assign({}, this.project);

    // Create the form group
    this.project_form = new FormGroup({
      project_type: new FormControl(),
      title: new FormControl(),
      description: new FormControl(),
      group: new FormControl(),
    });
    console.log(this.model);
  }

  submitProject() {

    let form_value = this.project_form.value;

    // Control for groups
    if (! form_value.group) {
      form_value.group = this.user.groups[0]._id;
    }
    // form_value._id = undefined;
    // console.log(form_value);
    // console.log(this.model);

    this.submitted = true;
    this.rest_service.submitProject(this.model)
                     .subscribe(
                       params => {
                         console.log(params);
                         // A problem connecting to REST server
                         // Submitted is over
                         this.submitted = false;
                         this.submit_error = params.error;
                         if (params.success) {
                           this.dialogRef.close(params);
                         } else {
                           this.submit_error = params.message;
                         }
                       });
  }

  deleteProject() {
    this.submitted = true;

    // Use REST service
    this.rest_service.deleteProject(this.project._id).subscribe(params => {
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
