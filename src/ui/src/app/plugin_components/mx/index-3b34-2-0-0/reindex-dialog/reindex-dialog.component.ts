import { Component,
         Inject,
         OnInit } from '@angular/core';
import { FormGroup,
         FormControl } from '@angular/forms';
import { MdDialogRef,
         MD_DIALOG_DATA } from '@angular/material';

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

  constructor(private globals_service: GlobalsService,
              public dialogRef: MdDialogRef<ReindexDialogComponent>,
              @Inject(MD_DIALOG_DATA) public data: any) { }

  ngOnInit() {

    console.log(this.data);

    this.model = {
      'spacegroup': this.data.preferences.spacegroup,
      'sample_type': this.data.preferences.sample_type
    };

    if (this.model.spacegroup === false) {
      this.model.spacegroup = 0;
    }

    this.reindex_form = new FormGroup({
      spacegroup: new FormControl(),
      sample_type: new FormControl(),
    });

  }

  submitReindex() {
    console.log(this.reindex_form.value);
  }

}
