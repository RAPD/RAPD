import { Component, 
         OnInit } from '@angular/core';
import { formatNumber } from '@angular/common';

@Component({
  selector: 'app-pdbquery9a2e100',
  templateUrl: './pdbquery9a2e100.component.html',
  styleUrls: ['./pdbquery9a2e100.component.css']
})
export class Pdbquery9a2e100Component implements OnInit {

  result: any = {"process": {"status": 90, "process_id": "c232db9a5eb511e8b0650cc47a63780c", "type": "plugin"}, "results": {"common_contaminants": {"3CLA": {"message": "No solution", "solution": false}}, "custom_structures": {}, "search_results": {"3V82": {"mtz": "3V82.1.mtz", "clash": 0.0, "tar": "/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_pdbquery_thau_free/3V82.tar.bz2", "nmol": 1, "tNCS": false, "rfz": 8.4, "solution": true, "adf": null, "gain": 11618.749279675354, "tfz": 20.0, "spacegroup": "P41212", "pdb": "3V82.1.pdb", "dir": "/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_pdbquery_thau_free/Phaser_3V82", "peak": null}, "3V88": {"mtz": "3V88.1.mtz", "clash": 0.0, "tar": "/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_pdbquery_thau_free/3V88.tar.bz2", "nmol": 1, "tNCS": false, "rfz": 8.3, "solution": true, "adf": null, "gain": 10127.636042102458, "tfz": 19.9, "spacegroup": "P41212", "pdb": "3V88.1.pdb", "dir": "/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_pdbquery_thau_free/Phaser_3V88", "peak": null}, "3V87": {"mtz": "3V87.1.mtz", "clash": 0.0, "tar": "/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_pdbquery_thau_free/3V87.tar.bz2", "nmol": 1, "tNCS": false, "rfz": 8.3, "solution": true, "adf": null, "gain": 11737.58688373464, "tfz": 20.0, "spacegroup": "P41212", "pdb": "3V87.1.pdb", "dir": "/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_pdbquery_thau_free/Phaser_3V87", "peak": null}}}, "command": {"status": 0, "preferences": {"search": true, "computer_cluster": true, "progress": false, "clean": true, "nproc": 8, "test": false, "contaminants": true, "run_mode": "server"}, "directories": {"work": "/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_pdbquery_thau_free"}, "input_data": {"datafile": "/gpfs6/users/necat/Jon/RAPD_test/Datasets/MR/thau_free.mtz", "pdbs": false, "db_settings": {"DATABASE_STRING": "mongodb://rapd:shallowkillerbeg@remote.nec.aps.anl.gov:27017,remote-c.nec.aps.anl.gov:27017,rapd.nec.aps.anl.gov:27017/rapd?replicaSet=rs0", "REDIS_SENTINEL_HOSTS": [["164.54.212.172", 26379], ["164.54.212.170", 26379], ["164.54.212.169", 26379], ["164.54.212.165", 26379], ["164.54.212.166", 26379]], "REDIS_HOST": "164.54.212.172", "CONTROL_DATABASE": "mongodb", "REDIS_DB": 0, "REDIS_PORT": 6379, "DATABASE_NAME_DATA": "rapd_data", "DATABASE_NAME_CLOUD": "rapd_cloud", "DATABASE_USER": "rapd", "DATABASE_NAME_USERS": "rapd_users", "REDIS_CONNECTION": "sentinel", "REDIS_MASTER_NAME": "remote_master", "DATABASE_PASSWORD": "shallowkillerbeg", "DATABASE_HOST": "164.54.212.169"}}, "process_id": "c232db9a5eb511e8b0650cc47a63780c", "command": "PDBQUERY"}, "preferences": {"search": true, "computer_cluster": true, "progress": false, "clean": true, "nproc": 8, "test": false, "contaminants": true, "run_mode": "server"}, "plugin": {"subtype": "EXPERIMENTAL", "version": "2.0.0", "type": "PDBQUERY", "id": "9a2e422625e811e79866ac87a3333966", "data_type": "MX"}};
  // raw_result: String;

  objectKeys = Object.keys;

  constructor() { }

  ngOnInit() { }

  default_val(val:any, default_val:any, digitsInfo: string = undefined) {
    // console.log('default_val', val, default_val, digitsInfo);
    if (val === undefined) {
      return default_val;
    } else if (isNaN(val)) {
      return val;
    } else if (digitsInfo) {
      return formatNumber(val, 'en-US', digitsInfo)
    } else {
      return val;
    }
  }

}
