import { Component,
         Inject,
         OnInit } from '@angular/core';
import { FormGroup,
        FormControl } from '@angular/forms';
import { MdDialogRef,
         MD_DIALOG_DATA } from '@angular/material';

import { RequestsService } from '../../../shared/services/requests.service';
import { GlobalsService } from '../../../shared/services/globals.service';

@Component({
  selector: 'app-reintegrate-dialog',
  templateUrl: './reintegrate-dialog.component.html',
  styleUrls: ['./reintegrate-dialog.component.css']
})
export class ReintegrateDialogComponent implements OnInit {

  submitted: boolean = false;
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
              private requests_service: RequestsService,
              public dialogRef: MdDialogRef<ReintegrateDialogComponent>,
              @Inject(MD_DIALOG_DATA) public data: any) { }

  ngOnInit() {
    console.log(this.data);

    this.model = {
      spacegroup: this.data.preferences.spacegroup,
      start_frame: 0, //this.data.preferences.spacegroup,
      end_frame: 360, //this.data.preferences.spacegroup,
      // sample_type: this.data.preferences.sample_type,
      rounds_polishing: this.data.preferences.rounds_polishing,
      spacegroup_decider: this.data.preferences.spacegroup_decider,
    };

    if (this.model.spacegroup === false) {
      this.model.spacegroup = 0;
    }

    this.reintegrate_form = new FormGroup({
      spacegroup: new FormControl(),
      start_frame: new FormControl(),
      end_frame: new FormControl(),
      sample_type: new FormControl(),
      rounds_polishing: new FormControl(),
      spacegroup_decider: new FormControl()
    });
  }

}
