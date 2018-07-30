import { Component, Input, OnInit, ViewChild } from "@angular/core";
import { formatNumber } from "@angular/common";
import { MatSort, MatSnackBar, MatTableDataSource } from "@angular/material";
// import { MatSortModule } from '@angular/material/sort';
import { RestService } from "../../../shared/services/rest.service";

@Component({
  selector: "app-pdbquery9a2e200",
  templateUrl: "./pdbquery9a2e200.component.html",
  styleUrls: ["./pdbquery9a2e200.component.css"]
})
export class Pdbquery9a2e200Component implements OnInit {
  // result: any = {"process": {"status": 90, "process_id": "c232db9a5eb511e8b0650cc47a63780c", "type": "plugin"}, "results": {"common_contaminants": {"3CLA": {"message": "No solution", "solution": false}}, "custom_structures": {}, "search_results": {"3V82": {"mtz": "3V82.1.mtz", "clash": 0.0, "tar": "/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_pdbquery_thau_free/3V82.tar.bz2", "nmol": 1, "tNCS": false, "rfz": 8.4, "solution": true, "adf": null, "gain": 11618.749279675354, "tfz": 20.0, "spacegroup": "P41212", "pdb": "3V82.1.pdb", "dir": "/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_pdbquery_thau_free/Phaser_3V82", "peak": null}, "3V88": {"mtz": "3V88.1.mtz", "clash": 0.0, "tar": "/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_pdbquery_thau_free/3V88.tar.bz2", "nmol": 1, "tNCS": false, "rfz": 8.3, "solution": true, "adf": null, "gain": 10127.636042102458, "tfz": 19.9, "spacegroup": "P41212", "pdb": "3V88.1.pdb", "dir": "/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_pdbquery_thau_free/Phaser_3V88", "peak": null}, "3V87": {"mtz": "3V87.1.mtz", "clash": 0.0, "tar": "/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_pdbquery_thau_free/3V87.tar.bz2", "nmol": 1, "tNCS": false, "rfz": 8.3, "solution": true, "adf": null, "gain": 11737.58688373464, "tfz": 20.0, "spacegroup": "P41212", "pdb": "3V87.1.pdb", "dir": "/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_pdbquery_thau_free/Phaser_3V87", "peak": null}}}, "command": {"status": 0, "preferences": {"search": true, "computer_cluster": true, "progress": false, "clean": true, "nproc": 8, "test": false, "contaminants": true, "run_mode": "server"}, "directories": {"work": "/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_pdbquery_thau_free"}, "input_data": {"datafile": "/gpfs6/users/necat/Jon/RAPD_test/Datasets/MR/thau_free.mtz", "pdbs": false, "db_settings": {"DATABASE_STRING": "mongodb://rapd:shallowkillerbeg@remote.nec.aps.anl.gov:27017,remote-c.nec.aps.anl.gov:27017,rapd.nec.aps.anl.gov:27017/rapd?replicaSet=rs0", "REDIS_SENTINEL_HOSTS": [["164.54.212.172", 26379], ["164.54.212.170", 26379], ["164.54.212.169", 26379], ["164.54.212.165", 26379], ["164.54.212.166", 26379]], "REDIS_HOST": "164.54.212.172", "CONTROL_DATABASE": "mongodb", "REDIS_DB": 0, "REDIS_PORT": 6379, "DATABASE_NAME_DATA": "rapd_data", "DATABASE_NAME_CLOUD": "rapd_cloud", "DATABASE_USER": "rapd", "DATABASE_NAME_USERS": "rapd_users", "REDIS_CONNECTION": "sentinel", "REDIS_MASTER_NAME": "remote_master", "DATABASE_PASSWORD": "shallowkillerbeg", "DATABASE_HOST": "164.54.212.169"}}, "process_id": "c232db9a5eb511e8b0650cc47a63780c", "command": "PDBQUERY"}, "preferences": {"search": true, "computer_cluster": true, "progress": false, "clean": true, "nproc": 8, "test": false, "contaminants": true, "run_mode": "server"}, "plugin": {"subtype": "EXPERIMENTAL", "version": "2.0.0", "type": "PDBQUERY", "id": "9a2e422625e811e79866ac87a3333966", "data_type": "MX"}};
  // result: any = {"process": {"status": 90, "process_id": "3795b7ea65c811e8b1190cc47a63780c", "type": "plugin"},
  //                "results": {"common_contaminants": {"3CLA": {"message": "No solution", "solution": false, "description": "TYPE III CHLORAMPHENICOL ACETYLTRANSFERASE"}}, "custom_structures": {"1111": {"message": "invalid PDB code", "solution": false, "description": "Unknown - PDB code not found in PDBQ server"}}, "search_results": {"3V82": {"mtz": "3V82.1.mtz", "clash": 0.0, "tar": "/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_pdbquery_thau_free/3V82.tar.bz2", "nmol": 1, "tNCS": false, "rfz": 8.4, "description": "Thaumatin I", "solution": true, "adf": null, "gain": 11618.749279675354, "tfz": 20.0, "spacegroup": "P41212", "pdb": "3V82.1.pdb", "dir": "/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_pdbquery_thau_free/Phaser_3V82", "peak": null}, "3V88": {"mtz": "3V88.1.mtz", "clash": 0.0, "tar": "/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_pdbquery_thau_free/3V88.tar.bz2", "nmol": 1, "tNCS": false, "rfz": 8.3, "description": "Thaumatin I", "solution": true, "adf": null, "gain": 10127.636042102458, "tfz": 19.9, "spacegroup": "P41212", "pdb": "3V88.1.pdb", "dir": "/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_pdbquery_thau_free/Phaser_3V88", "peak": null}, "3V87": {"mtz": "3V87.1.mtz", "clash": 0.0, "tar": "/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_pdbquery_thau_free/3V87.tar.bz2", "nmol": 1, "tNCS": false, "rfz": 8.3, "description": "Thaumatin I", "solution": true, "adf": null, "gain": 11737.58688373464, "tfz": 20.0, "spacegroup": "P41212", "pdb": "3V87.1.pdb", "dir": "/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_pdbquery_thau_free/Phaser_3V87", "peak": null}}}, "command": {"status": 0, "preferences": {"search": true, "computer_cluster": true, "progress": false, "clean": true, "nproc": 2, "test": true, "contaminants": true, "run_mode": "server"}, "directories": {"work": "/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_pdbquery_thau_free"}, "input_data": {"datafile": "/gpfs6/users/necat/Jon/RAPD_test/Datasets/MR/thau_free.mtz", "pdbs": ["1111"], "db_settings": {"DATABASE_STRING": "mongodb://rapd:shallowkillerbeg@remote.nec.aps.anl.gov:27017,remote-c.nec.aps.anl.gov:27017,rapd.nec.aps.anl.gov:27017/rapd?replicaSet=rs0", "REDIS_SENTINEL_HOSTS": [["164.54.212.172", 26379], ["164.54.212.170", 26379], ["164.54.212.169", 26379]], "REDIS_HOST": "164.54.212.172", "CONTROL_DATABASE": "mongodb", "REDIS_DB": 0, "REDIS_PORT": 6379, "DATABASE_NAME_DATA": "rapd_data", "DATABASE_NAME_CLOUD": "rapd_cloud", "DATABASE_NAME_USERS": "rapd_users", "REDIS_CONNECTION": "sentinel", "REDIS_MASTER_NAME": "remote_master"}}, "process_id": "3795b7ea65c811e8b1190cc47a63780c", "command": "PDBQUERY"}, "preferences": {"search": true, "computer_cluster": true, "progress": false, "clean": true, "nproc": 2, "test": true, "contaminants": true, "run_mode": "server"}, "plugin": {"subtype": "EXPERIMENTAL", "version": "2.0.0", "type": "PDBQUERY", "id": "9a2e422625e811e79866ac87a3333966", "data_type": "MX"}};
  @Input() result: any;
  objectKeys = Object.keys;

  contaminants: [any];
  searches: [any];
  customs: [any];

  columnsToDisplay = [
    "ID",
    "description",
    "gain",
    "rfz",
    "tfz",
    "clash",
    "actions"
  ];

  @ViewChild(MatSort) sort: MatSort;

  constructor(
    private rest_service: RestService,
    public snackBar: MatSnackBar
  ) {}

  ngOnInit() {
    this.contaminants = this.result.results.common_contaminants.slice();
    this.searches = this.result.results.search_results.slice();
    this.customs = this.result.results.custom_structures.slice();

    // Sort the data
    this.sortData({ active: "gain", direction: "desc" }, "contaminants");
    this.sortData({ active: "gain", direction: "desc" }, "searches");
    this.sortData({ active: "gain", direction: "desc" }, "customs");
  }

  default_val(val: any, default_val: any, digitsInfo: string = undefined) {
    // console.log('default_val', val, default_val, digitsInfo);
    if (val === undefined) {
      return default_val;
    } else if (isNaN(val)) {
      return val;
    } else if (digitsInfo) {
      return formatNumber(val, "en-US", digitsInfo);
    } else {
      return val;
    }
  }
  sortData(sort, data_type) {
    var data;

    // Get the right starting data
    if (data_type === "contaminants") {
      data = this.result.results.common_contaminants.slice();
    } else if (data_type === "searches") {
      data = this.result.results.search_results.slice();
    } else if (data_type === "customs") {
      data = this.result.results.custom_structures.slice();
    }

    // If not active or no sort, return as from server
    if (!sort.active || sort.direction === "") {
      this[data_type] = data;
      return;
    }

    // Sort the data and assign
    this[data_type] = data.sort((a, b) => {
      let isAsc = sort.direction == "asc";
      switch (sort.active) {
        case "ID":
          return compare(a.ID, b.ID, isAsc);
        case "gain":
          return compare(a.gain, b.gain, isAsc);
        default:
          return 0;
      }
    });
  }

  // Start the download of data
  public initDownload(record: any) {
    
    console.log('initDownload');
    
    // Signal that the request has been made
    this.snackBar.open("Download request submitted", "Ok", {
      duration: 2000
    });

    // TODO
    this.rest_service
      .getDownloadByHash(record.tar.hash, record.tar.path);
      // .subscribe(result => {}, error => {});
  }
}

function compare(a, b, isAsc) {
  if (a === undefined) {
    a = -1000;
  }
  if (b === undefined) {
    b = -1000;
  }
  return (a < b ? -1 : 1) * (isAsc ? 1 : -1);
}
