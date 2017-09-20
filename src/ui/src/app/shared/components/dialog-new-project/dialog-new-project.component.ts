import { Component,
         OnInit } from '@angular/core';
import { FormGroup,
         FormControl } from '@angular/forms';
import { MdDialogRef,
         MD_DIALOG_DATA } from '@angular/material';

import { RestService } from '../../services/rest.service';

@Component({
  selector: 'app-dialog-new-project',
  templateUrl: './dialog-new-project.component.html',
  styleUrls: ['./dialog-new-project.component.css']
})
export class DialogNewProjectComponent implements OnInit {

  private submit_error:string;
  private submitted:boolean = false;
  private model: any;
  private project_form: FormGroup;

  constructor(private rest_service: RestService,
              public dialogRef: MdDialogRef<DialogNewProjectComponent>) { }

  ngOnInit() {

    // Create the form group
    this.project_form = new FormGroup({});

  }

  submitNewProject() {

  }

}
