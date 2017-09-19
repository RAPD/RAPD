import { Component,
         Input,
         OnInit } from '@angular/core';
import { MdDialogRef,
         MD_DIALOG_DATA } from '@angular/material';

import { RestService } from '../../../shared/services/rest.service';

@Component({
  selector: 'app-dialog-select-project',
  templateUrl: './dialog-select-project.component.html',
  styleUrls: ['./dialog-select-project.component.css']
})
export class DialogSelectProjectComponent implements OnInit {

  @Input()
  result: any = {};

  constructor(public dialogRef: MdDialogRef<DialogSelectProjectComponent>,
              private rest_service: RestService) { }

  ngOnInit() {
  }

}
