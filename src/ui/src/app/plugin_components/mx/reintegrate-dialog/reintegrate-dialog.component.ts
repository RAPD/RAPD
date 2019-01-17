import { Component, Inject, OnInit } from "@angular/core";
import { FormGroup, FormControl } from "@angular/forms";
import { MatDialogRef, MAT_DIALOG_DATA, MatSnackBar } from "@angular/material";

import { RestService } from "../../../shared/services/rest.service";
import { GlobalsService } from "../../../shared/services/globals.service";

@Component({
  selector: "app-reintegrate-dialog",
  templateUrl: "./reintegrate-dialog.component.html",
  styleUrls: ["./reintegrate-dialog.component.css"]
})
export class ReintegrateDialogComponent implements OnInit {
  submitted: boolean = false;
  submit_error: string = "";
  model: any;
  reintegrate_form: FormGroup;

  sample_types = [
    { val: "protein", label: "Protein" },
    { val: "dna", label: "DNA" },
    { val: "rna", label: "RNA" },
    { val: "peptide", label: "Peptide" }
  ];

  spacegroup_deciders = [
    { val: "auto", label: "Automatic" },
    { val: "xds", label: "XDS" },
    { val: "pointless", label: "Pointless" }
  ];

  constructor(
    private globals_service: GlobalsService,
    private rest_service: RestService,
    public dialogRef: MatDialogRef<ReintegrateDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any,
    public snackBar: MatSnackBar
  ) {}

  ngOnInit() {
    console.log(this.data);

    this.model = {
      end_frame: 360,
      hi_res: this.data.preferences.hi_res,
      low_res: this.data.preferences.low_res,
      rounds_polishing: this.data.preferences.rounds_polishing || 1,
      spacegroup: this.data.preferences.spacegroup || 0,
      spacegroup_decider: this.data.preferences.spacegroup_decider || "auto",
      start_frame: 0
    };

    if (this.model.spacegroup === false) {
      this.model.spacegroup = 0;
    }

    if (this.model.low_res === 0) {
      this.model.low_res = "None";
    }

    if (this.model.hi_res === 0) {
      this.model.hi_res = "None";
    }

    this.reintegrate_form = new FormGroup({
      end_frame: new FormControl(),
      hi_res: new FormControl(),
      low_res: new FormControl(),
      rounds_polishing: new FormControl(),
      sample_type: new FormControl(),
      spacegroup: new FormControl(),
      spacegroup_decider: new FormControl(),
      start_frame: new FormControl(),
    });
  }

  private submitReintegrate() {
    /*
    command = {
                "command":"INTEGRATE",
                "process":{
                    "image_id":image1.get("_id"),
                    "parent_id":False,
                    "result_id":str(ObjectId()),
                    "run_id":run_data.get("_id"),
                    "session_id":session_id,
                    "status":0,
                    "type":"plugin"
                    },
                "directories":directories,
                "data": {
                    "image_data":image1,
                    "run_data":run_data
                },
                "site_parameters":self.site.BEAM_INFO[image1["site_tag"]],
                "preferences":{
                    "cleanup":False,
                    "json":False,
                    "exchange_dir":self.site.EXCHANGE_DIR,
                    "xdsinp":xdsinp
                },
            }
    */

    console.log(this.data);

    // Working on work directory
    // /gpfs6/users/necat/rapd2/integrate/2018-12-17/AKE004_9_2/wedge_1_360
    console.log(this.data.results.dir);

    // Start to make the request object
    let request: any = {
      command: "INTEGRATE",
      data: false,
      directories: {
        work: "reintegrate/2018-12-20/foobar1",
      },
      preferences: Object.assign(
        this.data.preferences,
        this.reintegrate_form.value
      ),
      process: {
        image_id: this.data.process.image_id,
        parent_id: this.data._id,
        run_id: this.data.process.run_id,
        session_id: this.data.process.session_id,
        status: 0,
        type: "plugin",
      },
      site_parameters: false,
    };

    // request.parent_result_id = this.data._id;

    // Update the preferences with the form values
    // request.preferences = Object.assign(this.data.preferences, this.reintegrate_form.value);

    // Debugging
    console.log(request);

    // this.submitted = true;
    // this.rest_service.submitJob(request).subscribe(parameters => {
    //   console.log(parameters);
    //   if (parameters.success === true) {
    //     let snackBarRef = this.snackBar.open(
    //       "Reintegrate request submitted",
    //       "Ok",
    //       {
    //         duration: 10000
    //       }
    //     );
    //     this.dialogRef.close(parameters);
    //   } else {
    //     this.submit_error = parameters.error;
    //   }
    // });
  }
}
