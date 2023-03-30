# RAPD

NB - This project is under development and is bleeding edge. Code should stabilize significantly June 2021.

A package for automated indexing, strategy, integration, analysis, & structure solution of macromolecular crystallographic data.

Currently we are building out capabilities to the commandline and adding detectors to the software.

Current commands:

* analyze - analyze an MX data set and perform pdbquery
* get_cif - get a CIF file from the PDB by 4-character code
* get_pdb - get a PDB file from the PDB by 4-character code
* hdf5_to_cbf - convert hdf5 files to CBF
* index - index MX data and calculate data collection strategies
* integrate - integrate MX data
* pdbquery - compare data to input structures, common contaminants, or structures in the PDB with similar unit cell parameters

Developer commands:
* generate - create new RAPD templated files
* print_detector - print image file information
* python - python CLI with full RAPD imports available
* test - test runnner for RAPD project
* version - prints the current installed RAPD version
* xds_to_dict - transforms an XDS.INP to a python dict for including in RAPD detector file

Current site detectors supported (more are coming):  
- APS
    - aps_gmca_dectris_eiger16m
    - lscat_dectris_eiger9m
    - lscat_dectris_eiger2_16m
    - lscat_rayonix_mx300
    - necat_dectris_eiger16m
    - necat_dectris_pilatus6mf
    - necat_dectris_eiger2_16m
    - sercat_rayonix_mx300hs


- UCLA
    - ucla_rigaku_raxisivpp

For instructions on installation and setup, see install/README.md
