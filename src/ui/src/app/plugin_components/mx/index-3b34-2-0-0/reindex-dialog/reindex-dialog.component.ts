import { Component,
         Inject,
         OnInit } from '@angular/core';
import { FormGroup,
         FormControl } from '@angular/forms';
import { MdDialogRef,
         MD_DIALOG_DATA } from '@angular/material';

import { RequestsService } from '../../../../shared/services/requests.service';
import { GlobalsService } from '../../../../shared/services/globals.service';

@Component({
  selector: 'app-reindex-dialog',
  templateUrl: './reindex-dialog.component.html',
  styleUrls: ['./reindex-dialog.component.css']
})
export class ReindexDialogComponent implements OnInit {

  submitted: boolean = false;
  model: any;
  reindex_form: FormGroup;

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
                private requests_service: RequestsService,
                public dialogRef: MdDialogRef<ReindexDialogComponent>,
                @Inject(MD_DIALOG_DATA) public data: any) { }

  ngOnInit() {

    // console.log(this.data);

    this.model = {
      spacegroup: this.data.preferences.spacegroup,
      sample_type: this.data.preferences.sample_type,
      solvent_content: this.data.preferences.solvent_content,
      strategy_type: this.data.preferences.strategy_type,
      best_complexity: this.data.preferences.best_complexity,
      mosflm_seg: this.data.preferences.mosflm_seg,
      mosflm_rot: this.data.preferences.mosflm_rot,
      mosflm_start: this.data.preferences.mosflm_start,
      mosflm_end: this.data.preferences.mosflm_end,
    };

    if (this.model.spacegroup === false) {
      this.model.spacegroup = 0;
    }

    this.reindex_form = new FormGroup({
      spacegroup: new FormControl(),
      sample_type: new FormControl(),
      solvent_content: new FormControl(),
      strategy_type: new FormControl(),
      best_complexity: new FormControl(),
      mosflm_seg: new FormControl(),
      mosflm_rot: new FormControl(),
      mosflm_start: new FormControl(),
      mosflm_end: new FormControl(),
    });

  }

  submitReindex() {

    // Start to make the request object
    let request: any = {};
    request.parent_result_id = this.data._id;
    request.image1_id = this.data.header1._id;

    // 2nd image?
    if (this.data.header2) {
      request.image2_id = this.data.header2._id;
    } else {
      request.image2_id = false;
    }

    // Update the preferences with the form values
    request.preferences = Object.assign(this.data.preferences, this.reindex_form.value);

    // Debugging
    // console.log(this.reindex_form.value);

    this.submitted = true;
    this.requests_service.submitRequest(request).subscribe(params => {
      console.log(params);
      this.submitted = false;
      if (params.success === true) {
        this.dialogRef.close();
      }
      // } else {
      //   this.error_message = params;
      // }
    });

      // this.dialogRef.close(this.reindex_form.value);

  }

}