import { Component,
         Inject,
         OnInit } from '@angular/core';
import { UntypedFormGroup,
         UntypedFormControl,
         Validators } from '@angular/forms';
import { MatDialog, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';

import { RestService } from '../../../../shared/services/rest.service';
import { GlobalsService } from '../../../../shared/services/globals.service';

@Component({
  selector: 'app-reindex-dialog',
  templateUrl: './reindex-dialog.component.html',
  styleUrls: ['./reindex-dialog.component.css']
})
export class ReindexDialogComponent implements OnInit {

  submitted: boolean = false;
  submit_error:string = '';
  model: any;
  reindex_form: UntypedFormGroup;

  sample_types = [
    {val:"protein",label:"Protein"},
    {val:'dna', label:'DNA'},
    {val:'rna', label:'RNA'},
    {val:'peptide', label:'Peptide'}];

    strategy_types = [
      {val:'best',label:'Best'},
      {val:'mosflm', label:'Mosflm'}];

    best_complexity = ['none', 'min', 'full'];

    mosflm_segs = [1,2,3,4,5];

    constructor(private globals_service: GlobalsService,
                private rest_service: RestService,
                public dialogRef: MatDialogRef<ReindexDialogComponent>,
                @Inject(MAT_DIALOG_DATA) public data: any,
                public snackBar: MatSnackBar) { }

  ngOnInit() {

    this.model = {
      beam_search: this.data.preferences.beam_search,
      best_complexity: this.data.preferences.best_complexity,
      sample_type: this.data.preferences.sample_type,
      solvent_content: this.data.preferences.solvent_content,
      spacegroup: this.data.preferences.spacegroup,
      strategy_type: this.data.preferences.strategy_type,
      mosflm_end: this.data.preferences.mosflm_end,
      mosflm_rot: this.data.preferences.mosflm_rot,
      mosflm_seg: this.data.preferences.mosflm_seg,
      mosflm_start: this.data.preferences.mosflm_start,
    };

    if (this.model.spacegroup === false) {
      this.model.spacegroup = 0;
    }

    this.reindex_form = new UntypedFormGroup({
      beam_search: new UntypedFormControl(this.model.beam_search,
                                   [Validators.min(0), Validators.max(10)]),
      best_complexity: new UntypedFormControl(),
      mosflm_end: new UntypedFormControl(this.model.mosflm_end,
                                  [Validators.min(0), Validators.max(360)]),
      mosflm_rot: new UntypedFormControl(this.model.mosflm_rot,
                                  [Validators.min(0), Validators.max(360)]),
      mosflm_seg: new UntypedFormControl(),
      mosflm_start: new UntypedFormControl(this.model.mosflm_start,
                                    [Validators.min(0), Validators.max(360)]),
      sample_type: new UntypedFormControl(),
      solvent_content: new UntypedFormControl(this.model.solvent_content,
                                       [Validators.min(0), Validators.max(1)]),
      spacegroup: new UntypedFormControl(),
      strategy_type: new UntypedFormControl(),
    });
  }

  submitReindex() {

    console.log(this.data);

    // Start to make the request object
    let request:any = {
      command:'INDEX',
      process:{
        image1_id: this.data.process.image1_id,
        image2_id: this.data.process.image2_id,
        parent_id: this.data.process.result_id,
        result_id: false,
        session_id: this.data.process.session_id,
        source: 'client',
        status: 0
      },
    };

    // If this is a child, then its parent is our parent
    if (this.data.process.parent_id) {
      request.process.parent_id = this.data.process.parent_id;
    }

    // Images
    request.image1 = this.data.image1;
    request.image2 = this.data.image2;

    // Directories is a copy from parent. Plugin will handle
    request.directories = this.data.results.directories;

    // Update the preferences with the form values
    request.preferences = Object.assign(this.data.preferences, this.reindex_form.value);
    request.preferences.spacegroup = parseInt(request.preferences.spacegroup, 10);


    // Set run mode
    request.preferences.run_mode = 'server';

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
                           let snackBarRef = this.snackBar.open('Reindex request submitted', 'Ok', {
                             duration: 2000,
                           });
                           this.dialogRef.close();
                         }
                       });
  }
}
