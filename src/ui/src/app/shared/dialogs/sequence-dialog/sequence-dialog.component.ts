// import { CdkTextareaAutosize } from "@angular/cdk/text-field";
import { Component, Input, NgZone, OnInit, ViewChild } from "@angular/core";
import { UntypedFormControl, UntypedFormGroup, Validators } from "@angular/forms";
import { MAT_DIALOG_DATA, MatDialogRef } from "@angular/material/dialog";
import { take } from "rxjs/operators";

@Component({
  selector: "app-sequence-dialog",
  templateUrl: "./sequence-dialog.component.html",
  styleUrls: ["./sequence-dialog.component.css"]
})
export class SequenceDialogComponent implements OnInit {
  // Inputs
  @Input() public dialogTitle: string;

  public submitError: string = "";

  public sequenceForm: UntypedFormGroup;
  // @ViewChild("autosize") public autosize: CdkTextareaAutosize;

  constructor(
    public dialogRef: MatDialogRef<SequenceDialogComponent>,
    private ngZone: NgZone
  ) {}

  public ngOnInit() {
    this.sequenceForm = new UntypedFormGroup({
      description: new UntypedFormControl(""),
      name: new UntypedFormControl("", Validators.required),
      sequence: new UntypedFormControl("", Validators.required)
    });
  }

  public submitSequence() {}

  // public triggerResize() {
  //   // Wait for changes to be applied, then trigger textarea resize.
  //   this.ngZone.onStable
  //     .pipe(take(1))
  //     .subscribe(() => this.autosize.resizeToFitContent(true));
  // }
}
