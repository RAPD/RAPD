import { Component, Inject, OnInit } from "@angular/core";
import {
  MAT_DIALOG_DATA,
  MatDialog,
  MatDialogRef
} from "@angular/material/dialog";

import { RestService } from "../../../shared/services/rest.service";

import { Viewer } from "uglymol";

@Component({
  selector: "app-dialog-uglymol",
  templateUrl: "./dialog-uglymol.component.html",
  styleUrls: ["./dialog-uglymol.component.css"]
})
export class DialogUglymolComponent implements OnInit {
  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    private restService: RestService
  ) {}

  ngOnInit() {
    console.log(this.data);

    // Instantiate Uglymol viewer
    const V = new Viewer({ viewer: "viewer", hud: "hud", help: "help" });

    // Load PDB
    this.restService.getPdb("1mru").subscribe(res => {
      // console.log(res);
      V.load_pdb_from_text(res);
      // V.load_from_pdbe("1qrv");
    });
    // V.load_pdb("http://localhost:3000/api/download_pdb/1qrv");

    // Load a map
    this.restService.getMap("1mru").subscribe(res => {
      console.log(res);
      V.load_map_from_buffer(res, {}); //, {format:"dsn6"});
      // V.load_from_pdbe("1qrv");
    });
  }
}
