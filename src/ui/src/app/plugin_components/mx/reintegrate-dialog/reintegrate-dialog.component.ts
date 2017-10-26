import { Component,
         Inject,
         OnInit } from '@angular/core';
import { FormGroup,
         FormControl } from '@angular/forms';
import { MatDialogRef,
         MAT_DIALOG_DATA,
         MatSnackBar } from '@angular/material';

import { RestService } from '../../../shared/services/rest.service';
import { GlobalsService } from '../../../shared/services/globals.service';

@Component({
  selector: 'app-reintegrate-dialog',
  templateUrl: './reintegrate-dialog.component.html',
  styleUrls: ['./reintegrate-dialog.component.css']
})
export class ReintegrateDialogComponent implements OnInit {

  submitted: boolean = false;
  submit_error: string = '';
  model: any;
  reintegrate_form: FormGroup;

  sample_types = [
    {val:'protein', label:'Protein'},
    {val:'dna', label:'DNA'},
    {val:'rna', label:'RNA'},
    {val:'peptide', label:'Peptide'}];

  spacegroup_deciders:[any] = [
    {val:'auto', label:'Automatic'},
    {val:'xds', label:'XDS'},
    {val:'pointless', label:'Pointless'}
  ]

  constructor(private globals_service: GlobalsService,
              private rest_service: RestService,
              public dialogRef: MatDialogRef<ReintegrateDialogComponent>,
              @Inject(MAT_DIALOG_DATA) public data: any,
              public snackBar: MatSnackBar) { }

  ngOnInit() {
    console.log(this.data);

    this.model = {
      spacegroup: this.data.preferences.spacegroup,
      start_frame: 0, //this.data.preferences.spacegroup,
      end_frame: 360, //this.data.preferences.spacegroup,
      rounds_polishing: this.data.preferences.rounds_polishing,
      spacegroup_decider: this.data.preferences.spacegroup_decider,
      low_res: this.data.preferences.low_res,
      hi_res: this.data.preferences.hi_res,
    };

    if (this.model.spacegroup === false) {
      this.model.spacegroup = 0;
    }

    if (this.model.low_res === 0) {
      this.model.low_res = 'None';
    }

    if (this.model.hi_res === 0) {
      this.model.hi_res = 'None';
    }

    this.reintegrate_form = new FormGroup({
      spacegroup: new FormControl(),
      start_frame: new FormControl(),
      end_frame: new FormControl(),
      sample_type: new FormControl(),
      rounds_polishing: new FormControl(),
      spacegroup_decider: new FormControl(),
      low_res: new FormControl(),
      hi_res: new FormControl()
    });
  }

  submitReintegrate() {

    // Start to make the request object
    let request: any = {command:'INTEGRATE'};
    request.parent_result_id = this.data._id;
    // request.image1_id = this.data.image1._id;
    //
    // // 2nd image?
    // if (this.data.image2) {
    //   request.image2_id = this.data.image2._id;
    // } else {
    //   request.image2_id = false;
    // }

    // Update the preferences with the form values
    request.preferences = Object.assign(this.data.preferences, this.reintegrate_form.value);

    // Debugging
    console.log(request);

    this.submitted = true;
    this.rest_service.submitJob(request)
                     .subscribe(
                       parameters => {
                         console.log(parameters);
                         // A problem connecting to REST server
                         // Submitted is over
                         this.submitted = false;
                         this.submit_error = parameters.error;
                         if (parameters.success) {
                           let snackBarRef = this.snackBar.open('Reintegrate request submitted', 'Ok', {
                             duration: 2000,
                           });
                           this.dialogRef.close();
                         }
                       });

  }
}
