import { Component,
         Input,
         OnInit } from '@angular/core';

import { FormGroup,
         FormControl } from '@angular/forms';

import { MatDialogRef,
         MAT_DIALOG_DATA } from '@angular/material';

import { Project } from '../../classes/project';
import { RestService } from '../../services/rest.service';

@Component({
  selector: 'app-dialog-new-project',
  templateUrl: './dialog-new-project.component.html',
  styleUrls: ['./dialog-new-project.component.css']
})
export class DialogNewProjectComponent implements OnInit {

  private profile: any;
  private submit_error:string;
  private submitted:boolean = false;
  @Input() project: Project;
  model: Project;
  // private model:any = {
  //   project_type:'mx',
  //   title:'',
  //   description:'',
  //   group:''
  // };
  private project_form: FormGroup;

  constructor(private rest_service: RestService,
              public dialogRef: MatDialogRef<DialogNewProjectComponent>) { }

  ngOnInit() {

    // Get the user profile
    this.profile = JSON.parse(localStorage.getItem('profile'));
    // this.model.group = this.profile.groups[0]._id;

    // Create the form group
    this.project_form = new FormGroup({
      project_type: new FormControl(),
      title: new FormControl(),
      description: new FormControl(),
      group: new FormControl(),
    });
  }

  submitProject() {

    let form_value = this.project_form.value;

    // Control for groups
    if (! form_value.group) {
      form_value.group = this.profile.groups[0]._id;
    }
    // form_value._id = undefined;
    console.log(form_value);
    console.log(this.model);
    return false;

    // this.submitted = true;
    // this.rest_service.submitProject(form_value)
    //                  .subscribe(
    //                    parameters => {
    //                      console.log(parameters);
    //                      // A problem connecting to REST server
    //                      // Submitted is over
    //                      this.submitted = false;
    //                      this.submit_error = parameters.error;
    //                      if (parameters.success) {
    //                        this.dialogRef.close(parameters.project);
    //                      }
    //                    });
  }

}
