'''
__author__ = "Jon Schuermann, Frank Murphy"
__copyright__ = "Copyright 2009,2010,2011 Cornell University"
__credits__ = ["Jon Schuermann","Frank Murphy","David Neau","Kay Perry","Surajit Banerjee"]
__license__ = "BSD-3-Clause"
__version__ = "0.9"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"
__date__ = "2011/03/23"
'''

def input():
    #construct test input    
    input = ["AUTOINDEX", 
             
    #This is an example input dict used for testing this script.             
    #Input dict file. If autoindexing from two images, just include a third dict section for the second image header. 
             
    {#"work": "/gpfs1/users/necat/Jon/process/Test_Rapd/Output",
     "work": "/gpfs6/users/necat/Jon/RAPD_test/Output",
     #"work": "/dev/shm/",
    }, 
    
    {"puck": "A", 
     "md2_aperture": "70", 
     "sample": "6", 
     "ring_mode": "324 Singlets/~1.1% Coupling/Cogging", 
     "osc_start": "180.000", 
     "wavelength": "0.9792", 
     "sql_date": "2009-08-19 17:09:15", 
     "image_prefix": "mg1_snap", 
     "size1": "3072", 
     "size2": "3072", 
     "detector_sn": "911", 
     "osc_range": "1.0", 
     "adc": "slow", 
     "beamline": "24_ID_C", 
     "axis": "phi", 
     "type": "unsigned_short", 
     "binning": "2x2", 
     #"binning": "none", 
     "byte_order": "little_endian", 
     "phi": "0.000", 
     "dim": "2", 
     "time": "1.00",  
     "twotheta": "0.00", 
     "date": "Wed Aug 19 17:09:15 2009",
     "adsc_number": "1", 
     "ID": "mg1_snap_99_001_1", 
     "pixel_size": "0.10259", 
     "distance": "500.00", 
     "run_number": "99", 
     "transmission": "10.0",  
     "ring_cur": "102.3", 
     "unif_ped": "1500", 
     "beam_center_x": "156.73",
     "beam_center_y": "155.95",
     "directory": "/gpfs3/users/cornell/Crane_Aug09/images/gabriela/mg",
     "fullname": "/gpfs6/users/GU/Herr_Nov11/images/Screenshots/N2W6a_PAIR_0_002.img",
     #"fullname": "/dev/shm/test_1_001.img",
     "header_bytes": " 1024", 
     "image_number": "001", 
     "ccd_image_saturation": "65535",
          
     #"mk3_phi":"0.0",
     #"mk3_kappa":"0.0",
     "STAC file1": '/gpfs6/users/necat/Jon/RAPD_test/DNA_mosflm.inp',
     "STAC file2": '/gpfs6/users/necat/Jon/RAPD_test/bestfile90.par',
     "correct.lp":'/gpfs6/users/necat/Jon/RAPD_test/CORRECT.LP',
     "dataset_repr":'junk_data',
     "axis_align": 'smart',    #smart,anom,multi,long,all,a,b,c,ab,ac,bc
     "flux":'1.6e11',
     "beam_size_x":"0.07",
     "beam_size_y":"0.03",
     "gauss_x":'0.03',
     "gauss_y":'0.01'     
    }, 

  
       
    {#"reference_data_id": 1,
     "reference_data_id": None,
     #"reference_data": [['/gpfs6/users/necat/Jon/RAPD_test/index09.mat', 0.0, 30.0, 'junk_1_1-30','P41212']],
     #"reference_data": [['/gpfs6/users/necat/Jon/RAPD_test/DNA_mosflm.inp','/gpfs6/users/necat/Jon/RAPD_test/bestfile.par']],
     "reference_data": [['/gpfs6/users/necat/Jon/RAPD_test/CORRECT.LP']],
     "min_exposure_per": "1", 
     "crystal_size_x": "100", 
     "crystal_size_y": "100",
     "crystal_size_z": "100", 
     "db_password": "necatuser",
     "numberMolAU": "1",
     "user_dir_override": "False",
     "shape": "2.0",
     "work_directory": "None", 
     "work_dir_override": "False", 
     "cluster_host": "164.54.212.165", 
     "beam_size_y": "0.02", 
     "beam_size_x": "0.07", 
     "sample_type": "Protein", 
     "best_complexity": "none",
     "numberResidues": "250", 
     "beamline": "C",
     "cluster_port": 50000,
     "aperture": "AUTO", 
     "db_name": "rapd1", 
     "user_directory": "None", 
     "susceptibility": "1.0", 
     "transmission": "AUTO",
     "anomalous": "False", 
     "index_hi_res": 0.0, 
     "db_user": "rapd1",
     "db_host": "penguin2.nec.aps.anl.gov",
     "max_exposure_tot": "None", 
     "spacegroup": "None",
     "solvent_content": 0.55,
     "beam_flip": "False",
     "multiprocessing":"True",
     "x_beam": "0",
     "y_beam": "0",
     "aimed_res": 0.0,
     "strategy_type": 'best',
     "mosflm_rot": 0.0,
     "mosflm_seg":1,
     "a":0.0,
     "b":0.0,
     "c":0.0,
     "alpha":0.0,
     "beta":0.0,
     "gamma":0.0,
     
     
                 },
     
    ('127.0.0.1',50001)]
    
    return (input)