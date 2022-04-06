#import cbf
import json
import shutil
import os
import redis
from redis import Redis
#from redis.sentinel import Sentinel
import time
from threading import Thread
from multiprocessing import Process, Queue, Event
import shlex
import subprocess
import re
from pprint import pprint
import inspect
import sys
import utils.archive as archive
#import plugins.analysis.plugin
import utils.log
import utils.processes as process
import datetime
import glob

#import streamUtils as Utils
#from cctbx.regression.tst_adp_aniso_restraints import fd

def connect_redis_manager_HA(name="remote_master"):
    # Set up redis connection
    hosts = (("164.54.212.172", 26379),
             ("164.54.212.170", 26379),
             ("164.54.212.169", 26379),
             ("164.54.212.165", 26379),
             ("164.54.212.166", 26379)
            )
    
    # Connect to the sentinels
    sentinel = Sentinel(hosts)
    # Get the master redis instance
    return(sentinel.master_for(name))

def connect_remote_redis():

    red = redis.Redis(host="164.54.212.169",
            port=6379,
            db=0)
    # Save the pool for a clean exit.
    return red

def connect_rapd2_redis():
    return redis.Redis(host="164.54.212.158")

def connect_sercat_redis():

    pool = redis.ConnectionPool(host="164.54.208.142",
    				port=6379,
    				db=0)
    # Save the pool for a clean exit.
    return redis.Redis(connection_pool=pool)

def connect_ft_redis():

    pool = redis.ConnectionPool(host="164.54.212.32",
            port=6379,
            db=0)
    # Save the pool for a clean exit.
    return redis.Redis(connection_pool=pool)
  
def connect_beamline():
    # C is 56, E is 125
    pool = redis.ConnectionPool(host="164.54.212.125",
            port=6379,
            db=0)
    # Save the pool for a clean exit.
    return redis.Redis(connection_pool=pool)

def processLocal(inp, logger=False, output=False):
    """
    Run job as subprocess on local machine.
    """

    # Logfile might be passed in
    if type(inp) == tuple:
        command, logfile = inp
    else:
        command = inp
        logfile = False

    # Run the process
    proc = subprocess.Popen(command,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    # Send back PID if have outlet
    if output:
        output.put(proc.pid)

    # Get the stdout and stderr from process
    stdout, stderr = proc.communicate()
    # print stdout
    # print stderr

    # Write out a log file, if name passed in
    if logfile:
        with open(logfile, "w") as out_file:
            out_file.write(stdout)
            out_file.write(stderr)

def clear_cluster():
    l = []
    inp = 'qstat'
    myoutput = subprocess.Popen(inp,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    for line in myoutput.stdout:
        split = line.split()
        #print split
        if len(split) == 8:
            #if split[2].split('-')[0] in ['INTE']:
              #l.append(split[0])
            if split[2].count('INDEX-'):
                l.append(split[0])
            #if split[4] == 'qw':
            #    l.append(split[0])
            
    for pid in l:
        print pid
        os.system('qdel %s'%pid)


#clear_cluster()
"""
MR_results0 = '{"pdb_file": "/gpfs6/users/necat/Jon/RAPD_test/Output/Phaser_test/rapd_mr_thau_free/P41212_all_0/P41212_all_0.1.pdb", "logs": {"phaser": "*************************************************************************************\n*** Phaser Module: AUTOMATED MOLECULAR REPLACEMENT                          2.6.0 ***\n*************************************************************************************\n\n*** Steps:\n***    Cell Content Analysis\n***    Anisotropy correction\n***    Translational NCS correction\n***    Rotation Function\n***    Translation Function\n***    Packing\n***    Refinement\n***    Final Refinement (if data higher resolution than search resolution)\n*** Number of search ensembles = 1\n*** Search Method: FAST\n*** Input Search Order:\n*** #1   model  \n*** Automatic (best predicted) search order WILL be used\n\nCPU Time: 0 days 0 hrs 0 mins 0.04 secs (      0.04 secs)\nFinished: Thu Oct  8 11:00:46 2020\n\n*************************************************************************************\n*** Phaser Module: CELL CONTENT ANALYSIS                                    2.6.0 ***\n*************************************************************************************\n\n   Space-Group Name (Hall Symbol): P 41 21 2 ( P 4abw 2nw)\n   Space-Group Number: 92\n   Unit Cell:   57.80   57.80  150.20   90.00   90.00   90.00\n\n--------------------\nSPACE GROUP ANALYSIS\n--------------------\n\n   Input Space Group: P 41 21 2\n\n   (a) Space groups derived by translation (screw) symmetry\n   --------------------------------------------------------\n   Z   Space Group          Hall Symbol                   \n   ----\n   8   P 41 21 2             P 4abw 2nw                   \n       P 4 2 2               P 4 2                        \n       P 4 21 2              P 4ab 2ab                    \n       P 41 2 2              P 4w 2c                      \n       P 42 2 2              P 4c 2                       \n       P 42 21 2             P 4n 2n                      \n       P 43 2 2              P 4cw 2c                     \n       P 43 21 2             P 4nw 2abw                   \n   ----\n\n   (b) Subgroups of (a) for perfect twinning expansions\n   ----------------------------------------------------\n   Z   Space Group          Hall Symbol                   \n   ----\n   1   P 1                   P 1                          \n   ---\n   2   P 1 2 1               P 2y                         \n       P 1 1 2               P 2y (z,x,y)                 \n       P 2 1 1               P 2y (y,z,x)                 \n       P 1 21 1              P 2yb                        \n       P 1 1 21              P 2yb (z,x,y)                \n       P 21 1 1              P 2yb (y,z,x)                \n   ---\n   4   P 2 2 2               P 2 2                        \n       P 2 2 21              P 2c 2                       \n       P 21 2 2              P 2c 2 (z,x,y)               \n       P 2 21 2              P 2c 2 (y,z,x)               \n       P 21 21 2             P 2 2ab                      \n       P 2 21 21             P 2 2ab (z,x,y)              \n       P 21 2 21             P 2 2ab (y,z,x)              \n       P 21 21 21            P 2ac 2ab                    \n       P 4                   P 4                          \n       P 41                  P 4w                         \n       P 42                  P 4c                         \n       P 43                  P 4cw                        \n   ----\n\n   Total Scattering = 88133.1\n   MW of \"average\" protein to which Matthews applies: 27028\n   Resolution for Matthews calculation:  1.69\n\n   Z       MW         VM    % solvent  rel. freq.\n   1       27028      2.32  47.01      1.000       <== most probable\n\n   Z is the number of multiples of the total composition\n   In most cases the most probable Z value should be 1\n   If it is not 1, you may need to consider other compositions\n\n   Histogram of relative frequencies of VM values\n   ----------------------------------------------\n   Frequency of most common VM value normalized to 1\n   VM values plotted in increments of 1/VM (0.02)\n\n        <--- relative frequency --->\n        0.0  0.1  0.2  0.3  0.4  0.5  0.6  0.7  0.8  0.9  1.0  \n        |    |    |    |    |    |    |    |    |    |    |    \n   10.00 -\n    8.33 -\n    7.14 -\n    6.25 -\n    5.56 -\n    5.00 -\n    4.55 -\n    4.17 -\n    3.85 -\n    3.57 --\n    3.33 ----\n    3.12 ------\n    2.94 -----------\n    2.78 -----------------\n    2.63 -------------------------\n    2.50 ----------------------------------\n    2.38 -------------------------------------------\n    2.27 ************************************************* (COMPOSITION*1)\n    2.17 --------------------------------------------------\n    2.08 --------------------------------------------\n    2.00 ---------------------------------\n    1.92 --------------------\n    1.85 ----------\n    1.79 ----\n    1.72 --\n    1.67 -\n    1.61 -\n    1.56 -\n    1.52 -\n    1.47 -\n    1.43 -\n    1.39 -\n    1.35 -\n    1.32 -\n    1.28 -\n    1.25 -\n\n   Most probable VM for resolution = 2.21161\n   Most probable MW of protein in asu for resolution = 28367\n\nCPU Time: 0 days 0 hrs 0 mins 0.13 secs (      0.13 secs)\nFinished: Thu Oct  8 11:00:46 2020\n\n*************************************************************************************\n*** Phaser Module: AUTOMATED MOLECULAR REPLACEMENT                          2.6.0 ***\n*************************************************************************************\n\n   Composition Table\n   -----------------\n   Total Scattering = 88133\n   Search occupancy factor = 1 (default)\n   Ensemble                        Frac.Scat.  (Search Frac.Scat.)\n   \"model\"                           81.15%          81.15%\n\nCPU Time: 0 days 0 hrs 0 mins 0.13 secs (      0.13 secs)\nFinished: Thu Oct  8 11:00:46 2020\n\n*************************************************************************************\n*** Phaser Module: ANISOTROPY CORRECTION                                    2.6.0 ***\n*************************************************************************************\n\n------------------------------\nDATA FOR ANISOTROPY CORRECTION\n------------------------------\n\n   Resolution of All Data (Number):        1.69  45.81 (28683)\n   Resolution of Selected Data (Number):   1.69  45.81 (28683)\n\n---------------------\nANISOTROPY CORRECTION\n---------------------\n\n   Protocol cycle #1 of 3\n   Refinement protocol for this macrocycle:\n   BIN SCALES: REFINE\n   ANISOTROPY: REFINE\n   SOLVENT K:  FIX\n   SOLVENT B:  FIX\n\n   Protocol cycle #2 of 3\n   Refinement protocol for this macrocycle:\n   BIN SCALES: REFINE\n   ANISOTROPY: REFINE\n   SOLVENT K:  FIX\n   SOLVENT B:  FIX\n\n   Protocol cycle #3 of 3\n   Refinement protocol for this macrocycle:\n   BIN SCALES: REFINE\n   ANISOTROPY: REFINE\n   SOLVENT K:  FIX\n   SOLVENT B:  FIX\n\n   Outliers with a probability less than 1e-06 will be rejected\n   There were 0 (0.0000%) reflections rejected\n\n   No reflections are outliers\n\n   Performing Minimization...\n      Done\n   --- Convergence before iteration limit (50) at cycle 6 ---\n   Start-this-macrocycle End-this-macrocycle Change-this-macrocycle\n     -330566.855           -330385.897               180.958\n\n   Principal components of anisotropic part of B affecting observed amplitudes:\n     eigenB (A^2)     direction cosines (orthogonal coordinates)\n         1.131             -0.0025   1.0000  -0.0000\n         1.131              1.0000   0.0025  -0.0000\n        -2.263              0.0000   0.0000   1.0000\n   Anisotropic deltaB (i.e. range of principal components):   3.394\n   Resharpening B (to restore strong direction of diffraction):  -2.263\n   Wilson scale applied to get observed intensities: 4.7322e-01\n\n   Outliers with a probability less than 1e-06 will be rejected\n   There were 0 (0.0000%) reflections rejected\n\n   No reflections are outliers\n\n   Performing Minimization...\n      Done\n   --- Convergence before iteration limit (50) at cycle 1 ---\n   Start-this-macrocycle End-this-macrocycle Change-this-macrocycle\n     -330385.897           -330385.876                 0.022\n\n   Principal components of anisotropic part of B affecting observed amplitudes:\n     eigenB (A^2)     direction cosines (orthogonal coordinates)\n         1.134             -0.0025   1.0000  -0.0000\n         1.134              1.0000   0.0025  -0.0000\n        -2.269              0.0000   0.0000   1.0000\n   Anisotropic deltaB (i.e. range of principal components):   3.403\n   Resharpening B (to restore strong direction of diffraction):  -2.269\n   Wilson scale applied to get observed intensities: 4.7322e-01\n\n   Outliers with a probability less than 1e-06 will be rejected\n   There were 0 (0.0000%) reflections rejected\n\n   No reflections are outliers\n\n   Performing Minimization...\n      Done\n   --- Convergence before iteration limit (50) at cycle 1 ---\n   Start-this-macrocycle End-this-macrocycle Change-this-macrocycle\n     -330385.876           -330385.870                 0.005\n\n   Principal components of anisotropic part of B affecting observed amplitudes:\n     eigenB (A^2)     direction cosines (orthogonal coordinates)\n         1.136             -0.0025   1.0000  -0.0000\n         1.136              1.0000   0.0025  -0.0000\n        -2.272              0.0000   0.0000   1.0000\n   Anisotropic deltaB (i.e. range of principal components):   3.408\n   Resharpening B (to restore strong direction of diffraction):  -2.272\n   Wilson scale applied to get observed intensities: 4.7322e-01\n\n   Refined Anisotropy Parameters\n   -----------------------------\n   Principal components of anisotropic part of B affecting observed amplitudes:\n     eigenB (A^2)     direction cosines (orthogonal coordinates)\n         1.136             -0.0025   1.0000  -0.0000\n         1.136              1.0000   0.0025  -0.0000\n        -2.272              0.0000   0.0000   1.0000\n   Anisotropic deltaB (i.e. range of principal components):   3.408\n   Resharpening B (to restore strong direction of diffraction):  -2.272\n   Wilson scale applied to get observed intensities: 4.7322e-01\n\n--------------\nABSOLUTE SCALE\n--------------\n\n   Scale factor to put input Fs on absolute scale\n   Wilson Scale:    1.45368\n   Wilson B-factor: 11.7711\n\n------------\nOUTPUT FILES\n------------\n\n   No files output\n\nCPU Time: 0 days 0 hrs 0 mins 11.84 secs (     11.84 secs)\nFinished: Thu Oct  8 11:00:57 2020\n\n*************************************************************************************\n*** Phaser Module: EXPECTED LLG OF ENSEMBLES                                2.6.0 ***\n*************************************************************************************\n\n   Resolution of Data:    1.686\n   Number of Reflections: 28683\n\n   eLLG Values Computed for All Data\n   ---------------------------------\n   target-reso: Resolution to achieve target eLLG of 120\n   Ensemble                   (frac/rms min-max/ expected LLG  ) target-reso\n   \"model\"                    (0.81/0.633-0.633/         1635.8)   5.811  \n\nCPU Time: 0 days 0 hrs 0 mins 11.89 secs (     11.89 secs)\nFinished: Thu Oct  8 11:00:57 2020\n\n*************************************************************************************\n*** Phaser Module: TRANSLATIONAL NON-CRYSTALLOGRAPHIC SYMMETRY              2.6.0 ***\n*************************************************************************************\n\n   Unit Cell:   57.80   57.80  150.20   90.00   90.00   90.00\n\n-------------------------------------\nDATA FOR TRANSLATIONAL NCS CORRECTION\n-------------------------------------\n\n   Intensity Moments for Data\n   --------------------------\n   2nd Moment = <E^4>/<E^2>^2 == <J^2>/<J>^2\n                        Untwinned   Perfect Twin\n   2nd Moment  Centric:    3.0          2.0\n   2nd Moment Acentric:    2.0          1.5\n                               Measured\n   2nd Moment  Centric:          2.84\n   2nd Moment Acentric:          1.98\n\n   Resolution for Twin Analysis (85% I/SIGI > 3): 2.04A (HiRes=1.69A)\n\n---------------------\nANISOTROPY CORRECTION\n---------------------\n\n   No refinement of parameters\n\n   Intensity Moments after Anisotropy Correction\n   ---------------------------------------------\n   2nd Moment = <E^4>/<E^2>^2 == <J^2>/<J>^2\n                        Untwinned   Perfect Twin\n   2nd Moment  Centric:    3.0          2.0\n   2nd Moment Acentric:    2.0          1.5\n                               Measured\n   2nd Moment  Centric:          2.79\n   2nd Moment Acentric:          1.97\n\n   Resolution for Twin Analysis (85% I/SIGI > 3): 2.04A (HiRes=1.69A)\n\n------------------------\nTRANSLATIONAL NCS VECTOR\n------------------------\n\n   Space Group :       P 41 21 2\n   Patterson Symmetry: P 4/m m m\n   Resolution of All Data (Number):        1.69  45.81 (28683)\n   Resolution of Patterson (Number):       5.00   9.93 (1112)\n   No translational ncs found or input\n\n   tNCS/Twin Detection Table\n   -------------------------\n   No NCS translation vector\n\n                                 -Second Moments-            --P-values--\n                                 Centric Acentric      untwinned  twin frac <5%\n   Theoretical for untwinned     3.00    2.00    \n   Theoretical for perfect twin  2.00    1.50    \n   Initial (data as input)       2.84    1.98+/-0.038  0.332      1         \n   After Anisotropy Correction   2.79    1.97+/-0.037  0.218      1         \n\n   Resolution for Twin Analysis (85% I/SIGI > 3): 2.04A (HiRes=1.69A)\n\n------------\nOUTPUT FILES\n------------\n\n   No files output\n\nCPU Time: 0 days 0 hrs 0 mins 15.93 secs (     15.93 secs)\nFinished: Thu Oct  8 11:01:01 2020\n\n*************************************************************************************\n*** Phaser Module: AUTOMATED MOLECULAR REPLACEMENT                          2.6.0 ***\n*************************************************************************************\n\n*** Z-score test for definite solution is ON\n*** Z-score test for stopping search is OFF\n*** Deep search is OFF\n\nCPU Time: 0 days 0 hrs 0 mins 15.93 secs (     15.93 secs)\nFinished: Thu Oct  8 11:01:01 2020\n\n*************************************************************************************\n*** Phaser Module: EXPERIMENTAL ERROR CORRECTION PREPARATION                2.6.0 ***\n*************************************************************************************\n\n---------------------\nANISOTROPY CORRECTION\n---------------------\n\n   No refinement of parameters\n\n------------------------\nTRANSLATIONAL NCS VECTOR\n------------------------\n\n   Space Group :       P 41 21 2\n   Patterson Symmetry: P 4/m m m\n   Resolution of All Data (Number):        1.69  45.81 (28683)\n   Resolution of Patterson (Number):       5.00   9.93 (1112)\n   No translational ncs found or input\n\n-----------------------------\nEXPERIMENTAL ERROR CORRECTION\n-----------------------------\n\n   Calculate Luzzati D factors accounting for observational error...\n\n   Data have been provided as French-Wilson amplitudes\n\n------------\nOUTPUT FILES\n------------\n\n   No files output\n\nCPU Time: 0 days 0 hrs 0 mins 20.00 secs (     20.00 secs)\nFinished: Thu Oct  8 11:01:06 2020\n\n*************************************************************************************\n*** Phaser Module: AUTOMATED MOLECULAR REPLACEMENT                          2.6.0 ***\n*************************************************************************************\n\n*** Search Order (next search *) (placed +):\n*** #1   model *\n\nCPU Time: 0 days 0 hrs 0 mins 20.00 secs (     20.00 secs)\nFinished: Thu Oct  8 11:01:06 2020\n\n*************************************************************************************\n*** Phaser Module: MOLECULAR REPLACEMENT ROTATION FUNCTION                  2.6.0 ***\n*************************************************************************************\n\n---------------------\nANISOTROPY CORRECTION\n---------------------\n\n   No refinement of parameters\n\n------------------------\nTRANSLATIONAL NCS VECTOR\n------------------------\n\n   Space Group :       P 41 21 2\n   Patterson Symmetry: P 4/m m m\n   Resolution of All Data (Number):        1.69  45.81 (28683)\n   Resolution of Patterson (Number):       5.00   9.93 (1112)\n   No translational ncs found or input\n\n--------------------------\nDATA FOR ROTATION FUNCTION\n--------------------------\n\n   High resolution limit input = 4.50\n\n   Outliers with a probability less than 1e-06 will be rejected\n   There were 0 (0.0000%) reflections rejected\n\n   No reflections are outliers\n\n   Resolution of All Data (Number):        1.69  45.81 (28683)\n   Resolution of Selected Data (Number):   4.50  45.81 (1738)\n\n-------------------\nWILSON DISTRIBUTION\n-------------------\n\n   Parameters set for Wilson log-likelihood calculation\n   E = 0 and variance 1 for each reflection\n   Without correction for SigF to the variances,\n      Wilson log(likelihood) = - number of acentrics (1137)\n                               - half number of centrics (601/2)\n                             = -1437\n   With correction for SigF,\n      Wilson log(likelihood) = -1400.55\n\n----------\nENSEMBLING\n----------\n\n   Ensemble Generation: model\n   --------------------------\n   Ensemble configured for structure factor interpolation\n   Ensemble configured to resolution 4.50\n   PDB file # 1: thau.pdb\n      This pdb file contains 1 model\n      The input RmsD of model #1 with respect to the real structure is 0.63\n\n   Electron Density Calculation\n   0%      100%\n   |=======| DONE\n\n   Weighting Structure Factors\n   0%                                                                   100%\n   |====================================================================| DONE\n\n   VRMS delta lower/upper limit = -0.350656 / 12.688216\n      RMSD upper limit(s): 3.62\n      RMSD lower limit(s): 0.23\n\n   Ensemble Generation\n   -------------------\n   Resolution of Ensembles: 4.50016\n   Ensemble        Scat% Radius Model# Rel-B Input-RMS Initial-Delta-VRMS Initial-RMS\n   model            81.2  21.50      1 -42.5     0.633              0.000       0.633\n\n   Ensemble Generation for Spherical Harmonic Decomposition: model\n   ---------------------------------------------------------------\n   Ensemble configured for spherical harmonic decomposition\n   Ensemble configured to resolution 4.50\n   PDB file # 1: thau.pdb\n      This pdb file contains 1 model\n      The input RmsD of model #1 with respect to the real structure is 0.63\n\n   Electron Density Calculation\n   0%      100%\n   |=======| DONE\n\n   Weighting Structure Factors\n   0%                100%\n   |=================| DONE\n\n   VRMS delta lower/upper limit = -0.350656 / 12.688216\n      RMSD upper limit(s): 3.62\n      RMSD lower limit(s): 0.23\n\n   Elmn for Search Ensemble\n   Elmn Calculation for Search Ensemble\n   0%                                                                      100%\n   |=======================================================================| DONE\n\n   Target Function: FAST LERF1\n\n-------------------------\nROTATION FUNCTION #1 OF 1\n-------------------------\n\n   Search Ensemble: model\n\n   Sampling: 5.99 degrees\n\n   SOLU SET \n   SOLU ENSEMBLE model VRMS DELTA +0.0000 RMSD 0.63 #VRMS 0.63\n\n   Spherical Harmonics\n   -------------------\n   Elmn for Data\n   Elmn Calculation for Data\n   0%                                                                          100%\n   |===========================================================================| DONE\n\n   Scanning the Range of Beta Angles\n   ---------------------------------\n   Clmn Calculation\n   0%                               100%\n   |================================| DONE\n\n   Top Peaks Without Clustering\n   Select peaks over 67.5% of top (i.e. 0.675*(top-mean)+mean)\n   There were 18 sites over 67.5% of top\n   18 peaks selected\n   The sites over 67.5% are:\n   #     Euler1 Euler2 Euler3    FSS   Z-score\n   1       16.9    1.8  341.5    100.000  8.83\n   2       77.2    1.8   14.1     96.782  8.55\n   3       28.6    3.4   61.2     96.582  8.53\n   #Sites = 18: output truncated to 3 sites\n\n   Top 18 rotations before clustering will be rescored\n   Calculating Likelihood for RF #1 of 1\n   0%                  100%\n   |===================| DONE\n\n   Mean and Standard Deviation\n   ---------------------------\n   Scoring 500 randomly sampled rotations\n   Generating Statistics for RF #1 of 1\n   0%                                                                       100%\n   |========================================================================| DONE\n\n   Highest Score (Z-score):  60.6647   (9.26)\n\n   Top Peaks With Clustering\n   Select peaks over 75% of top (i.e. 0.75*(top-mean)+mean)\n   There was 1 site over 75% of top\n   The sites over 75% are:\n   #     Euler1 Euler2 Euler3    LLG   Z-score Split #Group  FSS-this-ang/FSS-top\n   1       16.9    1.8  341.5     60.665  9.26   0.0      8    100.000/   100.000\n          106.9    1.8  341.5\n          196.9    1.8  341.5\n          286.9    1.8  341.5\n          343.1  178.2  161.5\n           73.1  178.2  161.5\n          163.1  178.2  161.5\n          253.1  178.2  161.5\n\n   Rotation Function Table: model\n   ------------------------------\n   (Z-scores from Fast Rotation Function)\n   #SET        Top    (Z)      Second    (Z)       Third    (Z)\n   1         60.66   9.26         ---    ---         ---    ---\n\n---------------\nFINAL SELECTION\n---------------\n\n   Select by Percentage of Top value: 75%\n   Top RF = 60.6647\n   Purge RF mean = -37.6886\n   Number of sets stored before final selection = 1\n   Number of solutions stored before final selection = 1\n   Number of sets stored (deleted) after final selection = 1 (0)\n   Number of solutions stored (deleted) after final selection = 1 (0)\n   Number used for purge  = 3\n\n   Rotation Function Final Selection Table\n   ---------------------------------------\n   Rotation list length by SET\n   SET#  Start Final Deleted Set (*)\n      1  1     1           -\n   ALL   1     1    \n\n------------\nOUTPUT FILES\n------------\n\n   No files output\n\nCPU Time: 0 days 0 hrs 0 mins 32.39 secs (     32.39 secs)\nFinished: Thu Oct  8 11:01:18 2020\n\n*************************************************************************************\n*** Phaser Module: MOLECULAR REPLACEMENT TRANSLATION FUNCTION               2.6.0 ***\n*************************************************************************************\n\n---------------------\nANISOTROPY CORRECTION\n---------------------\n\n   No refinement of parameters\n\n------------------------\nTRANSLATIONAL NCS VECTOR\n------------------------\n\n   Space Group :       P 41 21 2\n   Patterson Symmetry: P 4/m m m\n   Resolution of All Data (Number):        1.69  45.81 (28683)\n   Resolution of Patterson (Number):       5.00   9.93 (1112)\n   No translational ncs found or input\n\n-----------------------------\nDATA FOR TRANSLATION FUNCTION\n-----------------------------\n\n   Outliers with a probability less than 1e-06 will be rejected\n   There were 0 (0.0000%) reflections rejected\n\n   No reflections are outliers\n\n   Resolution of All Data (Number):        1.69  45.81 (28683)\n   Resolution of Selected Data (Number):   4.50  45.81 (1738)\n\n-------------------\nWILSON DISTRIBUTION\n-------------------\n\n   Parameters set for Wilson log-likelihood calculation\n   E = 0 and variance 1 for each reflection\n   Without correction for SigF to the variances,\n      Wilson log(likelihood) = - number of acentrics (1137)\n                               - half number of centrics (601/2)\n                             = -1437\n   With correction for SigF,\n      Wilson log(likelihood) = -1400.55\n\n------------------------\nALTERNATIVE SPACE GROUPS\n------------------------\n\n   Space Group(s) to be tested:\n     P 41 21 2\n\n----------\nENSEMBLING\n----------\n\n   Ensemble Generation\n   -------------------\n   Resolution of Ensembles: 4.50016\n   Ensemble        Scat% Radius Model# Rel-B Input-RMS Initial-Delta-VRMS Initial-RMS\n   model            81.2  21.50      1 -42.5     0.633              0.000       0.633\n\n---------------------\nTRANSLATION FUNCTIONS\n---------------------\n\n   Target Function: FAST LETF1\n   Sampling: 1.13 Angstroms\n\n----------------------------\nTRANSLATION FUNCTION #1 OF 1\n----------------------------\n\n   SOLU SET \n   SOLU SPAC P 41 21 2\n   SOLU TRIAL ENSEMBLE model EULER 16.917 1.830 341.488 RFZ 9.26\n   SOLU ENSEMBLE model VRMS DELTA +0.0000 RMSD 0.63 #VRMS 0.63\n\n   This set has one trial orientation\n\n   #TRIAL   Euler1 Euler2 Euler3   Ensemble\n        1     16.9    1.8  341.5   model               \n\n   Scoring 500 randomly sampled orientations and translations\n   Generating Statistics for TF SET #1 of 1\n   0% 100%\n   |==| DONE\n\n   Mean Score (Sigma):       -325.09   (36.31)\n\n   SET #1 of 1 TRIAL #1 of 1\n   -------------------------\n   Euler =   16.9    1.8  341.5, Ensemble = model\n\n   Doing Fast Translation Function FFT...\n      Done\n\n   New Top Fast Translation Function FSS = 786.88 (TFZ=20.4) at Trial #1\n\n   Top Peaks Without Clustering\n   Select peaks over 67.5% of top (i.e. 0.675*(top-mean)+mean)\n   There were 24 sites over 67.5% of top\n   24 peaks selected\n   The sites over 67.5% are:\n   #     Frac X Frac Y Frac Z    FSS   Z-score\n   1      0.972  0.987  0.002     786.88 20.41\n   2      0.974  0.985  0.923     412.03 10.41\n   3      0.973  0.984  0.158     399.73 10.08\n   #Sites = 24: output truncated to 3 sites\n\n   Top 24 translations before clustering will be rescored\n   Calculating Likelihood for TF SET #1 of 1 TRIAL #1 of 1\n   0%                        100%\n   |=========================| DONE\n\n   New Top (ML) Translation Function LLG = 506.41 (TFZ=22.9) at Trial #1\n   Top Peaks With Clustering\n   Select peaks over 75% of top (i.e. 0.75*(top-mean)+mean)\n   There were 13 sites over 75% of top\n   The sites over 75% are:\n   #     Frac X Frac Y Frac Z    LLG   Z-score Split #Group  FSS-this-xyz/FSS-top\n   1      0.972  0.987  0.002     506.41 20.41   0.0      1     786.88/    786.88\n   2      0.974  0.985  0.923      68.45 10.41  11.3      2     412.03/    412.03\n   3      0.970  0.484  0.002      67.78  9.55  28.2      1     379.88/    379.88\n   #SITES = 13: OUTPUT TRUNCATED TO 3 SITES\n\n   Translation Function Table\n   --------------------------\n   SET ROT*deep   Top   (Z)     Second   (Z)      Third   (Z) Ensemble SpaceGroup \n     1   1      506.4 20.41       68.5 10.41       67.8  9.55 model    P 41 21 2  \n   --- ---\n\n---------------\nFINAL SELECTION\n---------------\n\n   LLG will be used for purge, not FSS\n   Top TF  = 506.41\n   Top TFZ = 20.41\n   Mean TF = -325.09\n   Number used for purge  = 1\n   Cutoff for acceptance = 506.4\n      TFZ used for final selection = 10.2034\n         Number of solutions over TF final cutoff  = 0\n         Number of solutions over TFZ final cutoff = 1\n         Number of solutions over TF & TFZ cutoff  = 0\n   Number of solutions stored before final selection = 13\n   Number of solutions stored (deleted) after final selection = 1 (12)\n\n------------\nOUTPUT FILES\n------------\n\n   No files output\n\nCPU Time: 0 days 0 hrs 0 mins 37.55 secs (     37.55 secs)\nFinished: Thu Oct  8 11:01:23 2020\n\n*************************************************************************************\n*** Phaser Module: MOLECULAR REPLACEMENT PACKING ANALYSIS                   2.6.0 ***\n*************************************************************************************\n\n---------\nENSEMBLES\n---------\n\n   Packing Ensemble: model\n\n-----------------\nENSEMBLE SYMMETRY\n-----------------\n\n   Ensemble \"model\" Point Group: 1\n\n----------------------\nSTRUCTURES FOR PACKING\n----------------------\n\n   Packing will be performed with \"trace\" atoms. which are C-alphas for protein, P\n   and selected N for nucleic acid\n   If there are no trace atoms in the molecule(s) all atoms will be used in the\n   packing test\n   If the trace length exceeds 1000 atoms then the molecule(s) will be sampled on a\n   hexagonal grid and the clash distance increased in proportion to the size of the\n   hexagonal grid sampling\n   When an ensemble consists of more than one structure, the structure with the\n   highest homology is selected for packing and the structure trimmed of loops that\n   diverge more than 3A from other atoms in the ensemble\n\n   Ensemble: model\n   ---------------\n   All atoms =  1562\n   Structure with lowest rms = thau.pdb (0.63347)\n   Trace length = 207\n   Trace atoms clash if they are closer than 3.00 Angstroms\n\n----------------\nPACKING FUNCTION\n----------------\n\n   There is 1 solution to pack\n   Packing analysis\n   0% 100%\n   |==| DONE\n\n   Packing Table\n   -------------\n   Solutions accepted if total number of clashes <= 5% of trace atoms\n      i.e. total number of clashes <= 10\n   AND if number of clashes <= 5% of trace atoms for each ensemble\n      i.e. model: number of clashes <= 10\n   #in  #out Clashes Symm TF-SET  ROT TFpk#        TF    TFZ    SpaceGroup \n   1    Top1  0      NO       1     1    1        506.41 20.41  P 41 21 2  \n\n   1 accepted of 1 solutions\n\n------------\nOUTPUT FILES\n------------\n\n   No files output\n\nCPU Time: 0 days 0 hrs 0 mins 37.61 secs (     37.61 secs)\nFinished: Thu Oct  8 11:01:23 2020\n\n*************************************************************************************\n*** Phaser Module: MOLECULAR REPLACEMENT REFINEMENT AND PHASING             2.6.0 ***\n*************************************************************************************\n\n---------------------\nANISOTROPY CORRECTION\n---------------------\n\n   No refinement of parameters\n\n------------------------\nTRANSLATIONAL NCS VECTOR\n------------------------\n\n   Space Group :       P 41 21 2\n   Patterson Symmetry: P 4/m m m\n   Resolution of All Data (Number):        1.69  45.81 (28683)\n   Resolution of Patterson (Number):       5.00   9.93 (1112)\n   No translational ncs found or input\n\n-------------------------------\nDATA FOR REFINEMENT AND PHASING\n-------------------------------\n\n   Outliers with a probability less than 1e-06 will be rejected\n   There were 0 (0.0000%) reflections rejected\n\n   No reflections are outliers\n\n   Resolution of All Data (Number):        1.69  45.81 (28683)\n   Resolution of Selected Data (Number):   4.50  45.81 (1738)\n\n-------------------\nWILSON DISTRIBUTION\n-------------------\n\n   Parameters set for Wilson log-likelihood calculation\n   E = 0 and variance 1 for each reflection\n   Without correction for SigF to the variances,\n      Wilson log(likelihood) = - number of acentrics (1137)\n                               - half number of centrics (601/2)\n                             = -1437\n   With correction for SigF,\n      Wilson log(likelihood) = -1400.55\n\n----------\nENSEMBLING\n----------\n\n   Ensemble Generation\n   -------------------\n   Resolution of Ensembles: 4.50016\n   Ensemble        Scat% Radius Model# Rel-B Input-RMS Initial-Delta-VRMS Initial-RMS\n   model            81.2  21.50      1 -42.5     0.633              0.000       0.633\n\n----------\nREFINEMENT\n----------\n\n   Protocol cycle #1 of 1\n   Refinement protocol for this macrocycle:\n   ROTATION      : REFINE\n   TRANSLATION   : REFINE\n   BFACTOR       : REFINE\n   MODEL VRMS    : FIX\n   MAP CELL SCALE: FIX\n   MAP OFACTOR   : FIX\n   LAST ONLY     : FALSE\n\n   There is 1 solution to refine\n   Refining solutions\n   0% 100%\n   |==| DONE\n\n\n   REFINING SET # 1 OF 1\n   ---------------------\n   Initial Parameters:\n   SOLU SET \n   SOLU 6DIM ENSE model EULER 286.9 1.8 341.5 FRAC -0.51 0.53 -0.25 BFAC 0.00\n   SOLU ENSEMBLE model VRMS DELTA +0.0000 RMSD 0.63 #VRMS 0.63\n\n   Performing Minimization...\n      Done\n   --- Convergence before iteration limit (50) at cycle 11 ---\n   Start-this-macrocycle End-this-macrocycle Change-this-macrocycle\n         507.681               571.644                63.963\n\n   Final Parameters:\n   SOLU SET \n   SOLU 6DIM ENSE model EULER 313.6 0.6 315.5 FRAC -0.52 0.51 -0.25 BFAC -1.19\n   SOLU ENSEMBLE model VRMS DELTA +0.0000 RMSD 0.63 #VRMS 0.63\n\n---------------\nTFZ EQUIVALENTS\n---------------\n\n   Refined TFZ equivalents calculated\n   1 top TFZ equivalents calculated\n      1 (Topfiles)\n      0 with TFZ > 6 (TFZ for Possibly Solved)\n\n   TFZ equivalent calculation for top solution #1 of 1\n   ---------------------------------------------------\n      Solution #1 of 1\n\n   Generating Statistics\n   0%                                                                       100%\n   |========================================================================| DONE\n\n   Mean Score (Sigma):       -346.80   (39.28)\n   Refined TF/TFZ equivalent = 570.88/23.4 (Unrefined TF/TFZ=506.41/20.4)\n\n   Mean and Sigma after Refinement (for Purge)\n   -------------------------------------------\n   Scoring 500 randomly sampled orientations and translations\n\n   Generating Statistics\n   0% 100%\n   |==| DONE\n\n   Mean Score for Purge before Refinement:  -325.09\n   Mean Score for Purge after Refinement :  -346.80\n\n---------------\nFIND DUPLICATES\n---------------\n\n   Check for nearly equivalent solutions\n   Calculating Duplicates for 1 solutions\n   0% 100%\n   |==| DONE\n\n   No duplicate solutions found\n\n---------------------\nFIND TEMPLATE MATCHES\n---------------------\n\n   No Template Solution(s) for comparison\n\n---------------\nPURGE SELECTION\n---------------\n\n   Purge solutions according to highest LLG from Refinement\n   --------------------------------------------------------\n   Top LLG = 570.88\n   Mean LLG = -346.8\n   Percent used for purge = 75%\n      Cutoff for acceptance = 341.5\n   Number used for purge  = 1\n      Cutoff for acceptance = 570.9\n   Overall cutoff for acceptance (excluding high TFZ) = 570.9\n   Number of solutions stored before purge = 1\n   Number of solutions stored (deleted) after purge = 1 (0)\n\n-------\nRESULTS\n-------\n\n   Refinement Table (Sorted)\n   -------------------------\n   #out =#out #in =T (Start LLG Rval TFZ) (Refined LLG Rval TFZ==) SpaceGroup  Cntrst\n   Top1 ---   1           506.4 36.1 20.4        570.9 34.5 23.4   P 41 21 2     n/a \n\n   Refinement Table (Variance Ranges)\n   ----------------------------------\n   Range of delta-VRMS and VRMS given over current solution list (1 solution(s))\n   Ensemble        Model#   RMS   Delta-VRMS min/max  (VRMS min/max)\n   model                1   0.633   +0.000/+0.000    ( 0.633/ 0.633 )\n\n------------\nOUTPUT FILES\n------------\n\n   A sharpening B-factor of 100% of the isotropic B-factor in the direction of\n   smallest falloff (i.e. highest resolution) has been added to the anisotropically\n   corrected structure factors (FWT,DELFWT)\n\n   Calculation of Map Coefficients\n   -------------------------------\n   1 top map coefficients calculated\n\n   Map coefficient calculated for top solution #1\n   SOLU SPAC P 41 21 2\n   SOLU 6DIM ENSE model EULER 313.6 0.6 315.5 FRAC -0.52 0.51 -0.25 BFAC -1.19\n   SOLU ENSEMBLE model VRMS DELTA +0.0000 RMSD 0.63 #VRMS 0.63\n\n   No files output\n\nCPU Time: 0 days 0 hrs 0 mins 44.39 secs (     44.39 secs)\nFinished: Thu Oct  8 11:01:30 2020\n\n*************************************************************************************\n*** Phaser Module: AUTOMATED MOLECULAR REPLACEMENT                          2.6.0 ***\n*************************************************************************************\n\n*** Current is Best Solution (first search)\n*** Current solution has 1 component\n*** New Best LLG = 570.9 (resolution = 4.50)\n*** Best Component so far = model \n\nCPU Time: 0 days 0 hrs 0 mins 44.40 secs (     44.40 secs)\nFinished: Thu Oct  8 11:01:30 2020\n\n*************************************************************************************\n*** Phaser Module: AUTOMATED MOLECULAR REPLACEMENT                          2.6.0 ***\n*************************************************************************************\n\n*** Solutions will be refined to highest resolution\n\nCPU Time: 0 days 0 hrs 0 mins 45.72 secs (     45.72 secs)\nFinished: Thu Oct  8 11:01:31 2020\n\n*************************************************************************************\n*** Phaser Module: MOLECULAR REPLACEMENT REFINEMENT AND PHASING             2.6.0 ***\n*************************************************************************************\n\n---------------------\nANISOTROPY CORRECTION\n---------------------\n\n   No refinement of parameters\n\n------------------------\nTRANSLATIONAL NCS VECTOR\n------------------------\n\n   Space Group :       P 41 21 2\n   Patterson Symmetry: P 4/m m m\n   Resolution of All Data (Number):        1.69  45.81 (28683)\n   Resolution of Patterson (Number):       5.00   9.93 (1112)\n   No translational ncs found or input\n\n-------------------------------\nDATA FOR REFINEMENT AND PHASING\n-------------------------------\n\n   Outliers with a probability less than 1e-06 will be rejected\n   There were 0 (0.0000%) reflections rejected\n\n   No reflections are outliers\n\n   Resolution of All Data (Number):        1.69  45.81 (28683)\n   Resolution of Selected Data (Number):   1.69  45.81 (28683)\n\n-------------------\nWILSON DISTRIBUTION\n-------------------\n\n   Parameters set for Wilson log-likelihood calculation\n   E = 0 and variance 1 for each reflection\n   Without correction for SigF to the variances,\n      Wilson log(likelihood) = - number of acentrics (24422)\n                               - half number of centrics (4261/2)\n                             = -26552\n   With correction for SigF,\n      Wilson log(likelihood) = -27040.4\n\n----------\nENSEMBLING\n----------\n\n   Ensemble Generation: model\n   --------------------------\n   Ensemble configured for structure factor interpolation\n   Ensemble configured to resolution 1.69\n   PDB file # 1: thau.pdb\n      This pdb file contains 1 model\n      The input RmsD of model #1 with respect to the real structure is 0.63\n\n   Electron Density Calculation\n   0%      100%\n   |=======| DONE\n\n   Weighting Structure Factors\n   0%                                                                       100%\n   |========================================================================| DONE\n\n   VRMS delta lower/upper limit = -0.389990 / 12.688216\n      RMSD upper limit(s): 3.62\n      RMSD lower limit(s): 0.11\n\n   Ensemble Generation\n   -------------------\n   Resolution of Ensembles: 1.68633\n   Ensemble        Scat% Radius Model# Rel-B Input-RMS Initial-Delta-VRMS Initial-RMS\n   model            81.2  21.50      1  24.0     0.633              0.000       0.633\n\n----------\nREFINEMENT\n----------\n\n   Protocol cycle #1 of 1\n   Refinement protocol for this macrocycle:\n   ROTATION      : REFINE\n   TRANSLATION   : REFINE\n   BFACTOR       : REFINE\n   MODEL VRMS    : REFINE\n   MAP CELL SCALE: FIX\n   MAP OFACTOR   : FIX\n   LAST ONLY     : FALSE\n\n   There is 1 solution to refine\n   Refining solutions\n   0% 100%\n   |==| DONE\n\n\n   REFINING SET # 1 OF 1\n   ---------------------\n   Initial Parameters:\n   SOLU SET \n   SOLU 6DIM ENSE model EULER 313.6 0.6 315.5 FRAC -0.52 0.51 -0.25 BFAC -1.19\n   SOLU ENSEMBLE model VRMS DELTA +0.0000 RMSD 0.63 #VRMS 0.63\n\n   Performing Minimization...\n      Done\n   --- Convergence before iteration limit (50) at cycle 8 ---\n   Start-this-macrocycle End-this-macrocycle Change-this-macrocycle\n        5015.298              9297.113              4281.816\n\n   Final Parameters:\n   SOLU SET \n   SOLU 6DIM ENSE model EULER 310.4 0.7 318.7 FRAC -0.52 0.51 -0.25 BFAC -1.19\n   SOLU ENSEMBLE model VRMS DELTA -0.3227 RMSD 0.63 #VRMS 0.28\n\n---------------\nTFZ EQUIVALENTS\n---------------\n\n   Refined TFZ equivalents calculated\n   1 top TFZ equivalents calculated\n      1 (Topfiles)\n      0 with TFZ > 6 (TFZ for Possibly Solved)\n\n   TFZ equivalent calculation for top solution #1 of 1\n   ---------------------------------------------------\n      Solution #1 of 1\n\n   Generating Statistics\n   0%                                                                       100%\n   |========================================================================| DONE\n\n   Mean Score (Sigma):       -14187.35   (247.03)\n   Refined TF/TFZ equivalent = 9294.31/95.1 (Unrefined TF/TFZ=5014.76/23.4)\n\n   Mean and Sigma after Refinement (for Purge)\n   -------------------------------------------\n   Scoring 500 randomly sampled orientations and translations\n\n   Generating Statistics\n   0% 100%\n   |==| DONE\n\n   Mean Score for Purge before Refinement:  -346.80\n   Mean Score for Purge after Refinement :  -14187.35\n\n---------------\nFIND DUPLICATES\n---------------\n\n   Check for nearly equivalent solutions\n   Calculating Duplicates for 1 solutions\n   0% 100%\n   |==| DONE\n\n   No duplicate solutions found\n\n---------------------\nFIND TEMPLATE MATCHES\n---------------------\n\n   No Template Solution(s) for comparison\n\n---------------\nPURGE SELECTION\n---------------\n\n   Purge solutions according to highest LLG from Refinement\n   --------------------------------------------------------\n   Top LLG = 9294.31\n   Mean LLG = -14187.4\n   Percent used for purge = 75%\n      Cutoff for acceptance = 3423.9\n   Number used for purge  = 1\n      Cutoff for acceptance = 9294.3\n   Overall cutoff for acceptance (excluding high TFZ) = 9294.3\n   Number of solutions stored before purge = 1\n   Number of solutions stored (deleted) after purge = 1 (0)\n\n-------\nRESULTS\n-------\n\n   Refinement Table (Sorted)\n   -------------------------\n   Refinement to full resolution\n   #out =#out #in =T (Start LLG Rval TFZ) (Refined LLG Rval TFZ==) SpaceGroup  Cntrst\n   Top1 ---   1          5014.8 34.0 23.4       9294.3 33.6 95.1   P 41 21 2     n/a \n\n   Refinement Table (Variance Ranges)\n   ----------------------------------\n   Range of delta-VRMS and VRMS given over current solution list (1 solution(s))\n   Ensemble        Model#   RMS   Delta-VRMS min/max  (VRMS min/max)\n   model                1   0.633   -0.323/-0.323    ( 0.280/ 0.280 )\n\n------------\nOUTPUT FILES\n------------\n\n   A sharpening B-factor of 100% of the isotropic B-factor in the direction of\n   smallest falloff (i.e. highest resolution) has been added to the anisotropically\n   corrected structure factors (FWT,DELFWT)\n\n   Calculation of Map Coefficients\n   -------------------------------\n   1 top map coefficients calculated\n\n   Map coefficient calculated for top solution #1\n   SOLU SPAC P 41 21 2\n   SOLU 6DIM ENSE model EULER 310.4 0.7 318.7 FRAC -0.52 0.51 -0.25 BFAC -1.19\n   SOLU ENSEMBLE model VRMS DELTA -0.3227 RMSD 0.63 #VRMS 0.28\n\n   No files output\n\nCPU Time: 0 days 0 hrs 1 mins 59.00 secs (    119.00 secs)\nFinished: Thu Oct  8 11:02:44 2020\n\n*************************************************************************************\n*** Phaser Module: AUTOMATED MOLECULAR REPLACEMENT                          2.6.0 ***\n*************************************************************************************\n\n*** SINGLE solution\n\n*** Solution written to PDB file:  P41212_all_0.1.pdb\n*** Solution written to MTZ file:  P41212_all_0.1.mtz\n*** Solution annotation (history):\n   SOLU SET  RFZ=9.3 TFZ=20.4 PAK=0 LLG=571 TFZ==23.4 LLG=9294 TFZ==95.1\n   SOLU SPAC P 41 21 2\n   SOLU 6DIM ENSE model EULER 310.4 0.7 318.7 FRAC -0.52 0.51 -0.25 BFAC -1.19\n   SOLU ENSEMBLE model VRMS DELTA -0.3227 RMSD 0.63 #VRMS 0.28\n\nCPU Time: 0 days 0 hrs 1 mins 59.03 secs (    119.03 secs)\nFinished: Thu Oct  8 11:02:45 2020\n\n\n--------------------\nEXIT STATUS: SUCCESS\n--------------------\n\nCPU Time: 0 days 0 hrs 1 mins 59.03 secs (    119.03 secs)\nFinished: Thu Oct  8 11:02:45 2020\n\n</pre>\n</html>\n"}, "clash": 0.0, "tNCS": false, "gain": 9294.313971709074, "tfz": 20.4, "ID": "P41212_all_0", "map_1_1": {"path": "/gpfs6/users/necat/Jon/RAPD_test/Output/Phaser_test/rapd_mr_thau_free/P41212_all_0/P41212_all_0.1_mFo-DFc.ccp4.tar.bz2", "hash": "c2594b70b41b0f7e58e0ba3f97b7e46e7fcf8517", "description": "map_1_1"}, "mtz": {"path": "/gpfs6/users/necat/Jon/RAPD_test/Output/Phaser_test/rapd_mr_thau_free/P41212_all_0/P41212_all_0.1.mtz.tar.bz2", "hash": "d0ed3936ee117516f136ceadf66ce42f4dc604ab", "description": "mtz"}, "mtz_file": "/gpfs6/users/necat/Jon/RAPD_test/Output/Phaser_test/rapd_mr_thau_free/P41212_all_0/P41212_all_0.1.mtz", "tar": {"path": "/gpfs6/users/necat/Jon/RAPD_test/Output/Phaser_test/rapd_mr_thau_free/P41212_all_0/P41212_all_0.tar.bz2", "hash": "b567193c5eeb3eec71e762b779b1d9770ab85621", "description": "P41212_all_0_files"}, "nmol": 1, "rfz": 9.3, "map_2_1": {"path": "/gpfs6/users/necat/Jon/RAPD_test/Output/Phaser_test/rapd_mr_thau_free/P41212_all_0/P41212_all_0.1_2mFo-DFc.ccp4.tar.bz2", "hash": "c186bde77a05bf600ffbe0f2bdb0fb2c0d8144f5", "description": "map_2_1"}, "solution": true, "adf": null, "spacegroup": "P41212", "pdb": {"path": "/gpfs6/users/necat/Jon/RAPD_test/Output/Phaser_test/rapd_mr_thau_free/P41212_all_0/P41212_all_0.1.pdb.tar.bz2", "hash": "39312381fd225d35b846c8b6c906ef8648801e6e", "description": "pdb"}, "dir": "/gpfs6/users/necat/Jon/RAPD_test/Output/Phaser_test/rapd_mr_thau_free/P41212_all_0", "peak": null}'
MR_results1 = {"pdb_file": "/gpfs6/users/necat/Jon/RAPD_test/Output/Phaser_test/rapd_mr_thau_free/P41212_all_0/P41212_all_0.1.pdb", 
              "logs": {"phaser": "*************************************************************************************\n*** Phaser Module: AUTOMATED MOLECULAR REPLACEMENT                          2.6.0 ***\n*************************************************************************************\n\n*** Steps:\n***    Cell Content Analysis\n***    Anisotropy correction\n***    Translational NCS correction\n***    Rotation Function\n***    Translation Function\n***    Packing\n***    Refinement\n***    Final Refinement (if data higher resolution than search resolution)\n*** Number of search ensembles = 1\n*** Search Method: FAST\n*** Input Search Order:\n*** #1   model  \n*** Automatic (best predicted) search order WILL be used\n\nCPU Time: 0 days 0 hrs 0 mins 0.04 secs (      0.04 secs)\nFinished: Thu Oct  8 11:00:46 2020\n\n*************************************************************************************\n*** Phaser Module: CELL CONTENT ANALYSIS                                    2.6.0 ***\n*************************************************************************************\n\n   Space-Group Name (Hall Symbol): P 41 21 2 ( P 4abw 2nw)\n   Space-Group Number: 92\n   Unit Cell:   57.80   57.80  150.20   90.00   90.00   90.00\n\n--------------------\nSPACE GROUP ANALYSIS\n--------------------\n\n   Input Space Group: P 41 21 2\n\n   (a) Space groups derived by translation (screw) symmetry\n   --------------------------------------------------------\n   Z   Space Group          Hall Symbol                   \n   ----\n   8   P 41 21 2             P 4abw 2nw                   \n       P 4 2 2               P 4 2                        \n       P 4 21 2              P 4ab 2ab                    \n       P 41 2 2              P 4w 2c                      \n       P 42 2 2              P 4c 2                       \n       P 42 21 2             P 4n 2n                      \n       P 43 2 2              P 4cw 2c                     \n       P 43 21 2             P 4nw 2abw                   \n   ----\n\n   (b) Subgroups of (a) for perfect twinning expansions\n   ----------------------------------------------------\n   Z   Space Group          Hall Symbol                   \n   ----\n   1   P 1                   P 1                          \n   ---\n   2   P 1 2 1               P 2y                         \n       P 1 1 2               P 2y (z,x,y)                 \n       P 2 1 1               P 2y (y,z,x)                 \n       P 1 21 1              P 2yb                        \n       P 1 1 21              P 2yb (z,x,y)                \n       P 21 1 1              P 2yb (y,z,x)                \n   ---\n   4   P 2 2 2               P 2 2                        \n       P 2 2 21              P 2c 2                       \n       P 21 2 2              P 2c 2 (z,x,y)               \n       P 2 21 2              P 2c 2 (y,z,x)               \n       P 21 21 2             P 2 2ab                      \n       P 2 21 21             P 2 2ab (z,x,y)              \n       P 21 2 21             P 2 2ab (y,z,x)              \n       P 21 21 21            P 2ac 2ab                    \n       P 4                   P 4                          \n       P 41                  P 4w                         \n       P 42                  P 4c                         \n       P 43                  P 4cw                        \n   ----\n\n   Total Scattering = 88133.1\n   MW of \"average\" protein to which Matthews applies: 27028\n   Resolution for Matthews calculation:  1.69\n\n   Z       MW         VM    % solvent  rel. freq.\n   1       27028      2.32  47.01      1.000       <== most probable\n\n   Z is the number of multiples of the total composition\n   In most cases the most probable Z value should be 1\n   If it is not 1, you may need to consider other compositions\n\n   Histogram of relative frequencies of VM values\n   ----------------------------------------------\n   Frequency of most common VM value normalized to 1\n   VM values plotted in increments of 1/VM (0.02)\n\n        <--- relative frequency --->\n        0.0  0.1  0.2  0.3  0.4  0.5  0.6  0.7  0.8  0.9  1.0  \n        |    |    |    |    |    |    |    |    |    |    |    \n   10.00 -\n    8.33 -\n    7.14 -\n    6.25 -\n    5.56 -\n    5.00 -\n    4.55 -\n    4.17 -\n    3.85 -\n    3.57 --\n    3.33 ----\n    3.12 ------\n    2.94 -----------\n    2.78 -----------------\n    2.63 -------------------------\n    2.50 ----------------------------------\n    2.38 -------------------------------------------\n    2.27 ************************************************* (COMPOSITION*1)\n    2.17 --------------------------------------------------\n    2.08 --------------------------------------------\n    2.00 ---------------------------------\n    1.92 --------------------\n    1.85 ----------\n    1.79 ----\n    1.72 --\n    1.67 -\n    1.61 -\n    1.56 -\n    1.52 -\n    1.47 -\n    1.43 -\n    1.39 -\n    1.35 -\n    1.32 -\n    1.28 -\n    1.25 -\n\n   Most probable VM for resolution = 2.21161\n   Most probable MW of protein in asu for resolution = 28367\n\nCPU Time: 0 days 0 hrs 0 mins 0.13 secs (      0.13 secs)\nFinished: Thu Oct  8 11:00:46 2020\n\n*************************************************************************************\n*** Phaser Module: AUTOMATED MOLECULAR REPLACEMENT                          2.6.0 ***\n*************************************************************************************\n\n   Composition Table\n   -----------------\n   Total Scattering = 88133\n   Search occupancy factor = 1 (default)\n   Ensemble                        Frac.Scat.  (Search Frac.Scat.)\n   \"model\"                           81.15%          81.15%\n\nCPU Time: 0 days 0 hrs 0 mins 0.13 secs (      0.13 secs)\nFinished: Thu Oct  8 11:00:46 2020\n\n*************************************************************************************\n*** Phaser Module: ANISOTROPY CORRECTION                                    2.6.0 ***\n*************************************************************************************\n\n------------------------------\nDATA FOR ANISOTROPY CORRECTION\n------------------------------\n\n   Resolution of All Data (Number):        1.69  45.81 (28683)\n   Resolution of Selected Data (Number):   1.69  45.81 (28683)\n\n---------------------\nANISOTROPY CORRECTION\n---------------------\n\n   Protocol cycle #1 of 3\n   Refinement protocol for this macrocycle:\n   BIN SCALES: REFINE\n   ANISOTROPY: REFINE\n   SOLVENT K:  FIX\n   SOLVENT B:  FIX\n\n   Protocol cycle #2 of 3\n   Refinement protocol for this macrocycle:\n   BIN SCALES: REFINE\n   ANISOTROPY: REFINE\n   SOLVENT K:  FIX\n   SOLVENT B:  FIX\n\n   Protocol cycle #3 of 3\n   Refinement protocol for this macrocycle:\n   BIN SCALES: REFINE\n   ANISOTROPY: REFINE\n   SOLVENT K:  FIX\n   SOLVENT B:  FIX\n\n   Outliers with a probability less than 1e-06 will be rejected\n   There were 0 (0.0000%) reflections rejected\n\n   No reflections are outliers\n\n   Performing Minimization...\n      Done\n   --- Convergence before iteration limit (50) at cycle 6 ---\n   Start-this-macrocycle End-this-macrocycle Change-this-macrocycle\n     -330566.855           -330385.897               180.958\n\n   Principal components of anisotropic part of B affecting observed amplitudes:\n     eigenB (A^2)     direction cosines (orthogonal coordinates)\n         1.131             -0.0025   1.0000  -0.0000\n         1.131              1.0000   0.0025  -0.0000\n        -2.263              0.0000   0.0000   1.0000\n   Anisotropic deltaB (i.e. range of principal components):   3.394\n   Resharpening B (to restore strong direction of diffraction):  -2.263\n   Wilson scale applied to get observed intensities: 4.7322e-01\n\n   Outliers with a probability less than 1e-06 will be rejected\n   There were 0 (0.0000%) reflections rejected\n\n   No reflections are outliers\n\n   Performing Minimization...\n      Done\n   --- Convergence before iteration limit (50) at cycle 1 ---\n   Start-this-macrocycle End-this-macrocycle Change-this-macrocycle\n     -330385.897           -330385.876                 0.022\n\n   Principal components of anisotropic part of B affecting observed amplitudes:\n     eigenB (A^2)     direction cosines (orthogonal coordinates)\n         1.134             -0.0025   1.0000  -0.0000\n         1.134              1.0000   0.0025  -0.0000\n        -2.269              0.0000   0.0000   1.0000\n   Anisotropic deltaB (i.e. range of principal components):   3.403\n   Resharpening B (to restore strong direction of diffraction):  -2.269\n   Wilson scale applied to get observed intensities: 4.7322e-01\n\n   Outliers with a probability less than 1e-06 will be rejected\n   There were 0 (0.0000%) reflections rejected\n\n   No reflections are outliers\n\n   Performing Minimization...\n      Done\n   --- Convergence before iteration limit (50) at cycle 1 ---\n   Start-this-macrocycle End-this-macrocycle Change-this-macrocycle\n     -330385.876           -330385.870                 0.005\n\n   Principal components of anisotropic part of B affecting observed amplitudes:\n     eigenB (A^2)     direction cosines (orthogonal coordinates)\n         1.136             -0.0025   1.0000  -0.0000\n         1.136              1.0000   0.0025  -0.0000\n        -2.272              0.0000   0.0000   1.0000\n   Anisotropic deltaB (i.e. range of principal components):   3.408\n   Resharpening B (to restore strong direction of diffraction):  -2.272\n   Wilson scale applied to get observed intensities: 4.7322e-01\n\n   Refined Anisotropy Parameters\n   -----------------------------\n   Principal components of anisotropic part of B affecting observed amplitudes:\n     eigenB (A^2)     direction cosines (orthogonal coordinates)\n         1.136             -0.0025   1.0000  -0.0000\n         1.136              1.0000   0.0025  -0.0000\n        -2.272              0.0000   0.0000   1.0000\n   Anisotropic deltaB (i.e. range of principal components):   3.408\n   Resharpening B (to restore strong direction of diffraction):  -2.272\n   Wilson scale applied to get observed intensities: 4.7322e-01\n\n--------------\nABSOLUTE SCALE\n--------------\n\n   Scale factor to put input Fs on absolute scale\n   Wilson Scale:    1.45368\n   Wilson B-factor: 11.7711\n\n------------\nOUTPUT FILES\n------------\n\n   No files output\n\nCPU Time: 0 days 0 hrs 0 mins 11.84 secs (     11.84 secs)\nFinished: Thu Oct  8 11:00:57 2020\n\n*************************************************************************************\n*** Phaser Module: EXPECTED LLG OF ENSEMBLES                                2.6.0 ***\n*************************************************************************************\n\n   Resolution of Data:    1.686\n   Number of Reflections: 28683\n\n   eLLG Values Computed for All Data\n   ---------------------------------\n   target-reso: Resolution to achieve target eLLG of 120\n   Ensemble                   (frac/rms min-max/ expected LLG  ) target-reso\n   \"model\"                    (0.81/0.633-0.633/         1635.8)   5.811  \n\nCPU Time: 0 days 0 hrs 0 mins 11.89 secs (     11.89 secs)\nFinished: Thu Oct  8 11:00:57 2020\n\n*************************************************************************************\n*** Phaser Module: TRANSLATIONAL NON-CRYSTALLOGRAPHIC SYMMETRY              2.6.0 ***\n*************************************************************************************\n\n   Unit Cell:   57.80   57.80  150.20   90.00   90.00   90.00\n\n-------------------------------------\nDATA FOR TRANSLATIONAL NCS CORRECTION\n-------------------------------------\n\n   Intensity Moments for Data\n   --------------------------\n   2nd Moment = <E^4>/<E^2>^2 == <J^2>/<J>^2\n                        Untwinned   Perfect Twin\n   2nd Moment  Centric:    3.0          2.0\n   2nd Moment Acentric:    2.0          1.5\n                               Measured\n   2nd Moment  Centric:          2.84\n   2nd Moment Acentric:          1.98\n\n   Resolution for Twin Analysis (85% I/SIGI > 3): 2.04A (HiRes=1.69A)\n\n---------------------\nANISOTROPY CORRECTION\n---------------------\n\n   No refinement of parameters\n\n   Intensity Moments after Anisotropy Correction\n   ---------------------------------------------\n   2nd Moment = <E^4>/<E^2>^2 == <J^2>/<J>^2\n                        Untwinned   Perfect Twin\n   2nd Moment  Centric:    3.0          2.0\n   2nd Moment Acentric:    2.0          1.5\n                               Measured\n   2nd Moment  Centric:          2.79\n   2nd Moment Acentric:          1.97\n\n   Resolution for Twin Analysis (85% I/SIGI > 3): 2.04A (HiRes=1.69A)\n\n------------------------\nTRANSLATIONAL NCS VECTOR\n------------------------\n\n   Space Group :       P 41 21 2\n   Patterson Symmetry: P 4/m m m\n   Resolution of All Data (Number):        1.69  45.81 (28683)\n   Resolution of Patterson (Number):       5.00   9.93 (1112)\n   No translational ncs found or input\n\n   tNCS/Twin Detection Table\n   -------------------------\n   No NCS translation vector\n\n                                 -Second Moments-            --P-values--\n                                 Centric Acentric      untwinned  twin frac <5%\n   Theoretical for untwinned     3.00    2.00    \n   Theoretical for perfect twin  2.00    1.50    \n   Initial (data as input)       2.84    1.98+/-0.038  0.332      1         \n   After Anisotropy Correction   2.79    1.97+/-0.037  0.218      1         \n\n   Resolution for Twin Analysis (85% I/SIGI > 3): 2.04A (HiRes=1.69A)\n\n------------\nOUTPUT FILES\n------------\n\n   No files output\n\nCPU Time: 0 days 0 hrs 0 mins 15.93 secs (     15.93 secs)\nFinished: Thu Oct  8 11:01:01 2020\n\n*************************************************************************************\n*** Phaser Module: AUTOMATED MOLECULAR REPLACEMENT                          2.6.0 ***\n*************************************************************************************\n\n*** Z-score test for definite solution is ON\n*** Z-score test for stopping search is OFF\n*** Deep search is OFF\n\nCPU Time: 0 days 0 hrs 0 mins 15.93 secs (     15.93 secs)\nFinished: Thu Oct  8 11:01:01 2020\n\n*************************************************************************************\n*** Phaser Module: EXPERIMENTAL ERROR CORRECTION PREPARATION                2.6.0 ***\n*************************************************************************************\n\n---------------------\nANISOTROPY CORRECTION\n---------------------\n\n   No refinement of parameters\n\n------------------------\nTRANSLATIONAL NCS VECTOR\n------------------------\n\n   Space Group :       P 41 21 2\n   Patterson Symmetry: P 4/m m m\n   Resolution of All Data (Number):        1.69  45.81 (28683)\n   Resolution of Patterson (Number):       5.00   9.93 (1112)\n   No translational ncs found or input\n\n-----------------------------\nEXPERIMENTAL ERROR CORRECTION\n-----------------------------\n\n   Calculate Luzzati D factors accounting for observational error...\n\n   Data have been provided as French-Wilson amplitudes\n\n------------\nOUTPUT FILES\n------------\n\n   No files output\n\nCPU Time: 0 days 0 hrs 0 mins 20.00 secs (     20.00 secs)\nFinished: Thu Oct  8 11:01:06 2020\n\n*************************************************************************************\n*** Phaser Module: AUTOMATED MOLECULAR REPLACEMENT                          2.6.0 ***\n*************************************************************************************\n\n*** Search Order (next search *) (placed +):\n*** #1   model *\n\nCPU Time: 0 days 0 hrs 0 mins 20.00 secs (     20.00 secs)\nFinished: Thu Oct  8 11:01:06 2020\n\n*************************************************************************************\n*** Phaser Module: MOLECULAR REPLACEMENT ROTATION FUNCTION                  2.6.0 ***\n*************************************************************************************\n\n---------------------\nANISOTROPY CORRECTION\n---------------------\n\n   No refinement of parameters\n\n------------------------\nTRANSLATIONAL NCS VECTOR\n------------------------\n\n   Space Group :       P 41 21 2\n   Patterson Symmetry: P 4/m m m\n   Resolution of All Data (Number):        1.69  45.81 (28683)\n   Resolution of Patterson (Number):       5.00   9.93 (1112)\n   No translational ncs found or input\n\n--------------------------\nDATA FOR ROTATION FUNCTION\n--------------------------\n\n   High resolution limit input = 4.50\n\n   Outliers with a probability less than 1e-06 will be rejected\n   There were 0 (0.0000%) reflections rejected\n\n   No reflections are outliers\n\n   Resolution of All Data (Number):        1.69  45.81 (28683)\n   Resolution of Selected Data (Number):   4.50  45.81 (1738)\n\n-------------------\nWILSON DISTRIBUTION\n-------------------\n\n   Parameters set for Wilson log-likelihood calculation\n   E = 0 and variance 1 for each reflection\n   Without correction for SigF to the variances,\n      Wilson log(likelihood) = - number of acentrics (1137)\n                               - half number of centrics (601/2)\n                             = -1437\n   With correction for SigF,\n      Wilson log(likelihood) = -1400.55\n\n----------\nENSEMBLING\n----------\n\n   Ensemble Generation: model\n   --------------------------\n   Ensemble configured for structure factor interpolation\n   Ensemble configured to resolution 4.50\n   PDB file # 1: thau.pdb\n      This pdb file contains 1 model\n      The input RmsD of model #1 with respect to the real structure is 0.63\n\n   Electron Density Calculation\n   0%      100%\n   |=======| DONE\n\n   Weighting Structure Factors\n   0%                                                                   100%\n   |====================================================================| DONE\n\n   VRMS delta lower/upper limit = -0.350656 / 12.688216\n      RMSD upper limit(s): 3.62\n      RMSD lower limit(s): 0.23\n\n   Ensemble Generation\n   -------------------\n   Resolution of Ensembles: 4.50016\n   Ensemble        Scat% Radius Model# Rel-B Input-RMS Initial-Delta-VRMS Initial-RMS\n   model            81.2  21.50      1 -42.5     0.633              0.000       0.633\n\n   Ensemble Generation for Spherical Harmonic Decomposition: model\n   ---------------------------------------------------------------\n   Ensemble configured for spherical harmonic decomposition\n   Ensemble configured to resolution 4.50\n   PDB file # 1: thau.pdb\n      This pdb file contains 1 model\n      The input RmsD of model #1 with respect to the real structure is 0.63\n\n   Electron Density Calculation\n   0%      100%\n   |=======| DONE\n\n   Weighting Structure Factors\n   0%                100%\n   |=================| DONE\n\n   VRMS delta lower/upper limit = -0.350656 / 12.688216\n      RMSD upper limit(s): 3.62\n      RMSD lower limit(s): 0.23\n\n   Elmn for Search Ensemble\n   Elmn Calculation for Search Ensemble\n   0%                                                                      100%\n   |=======================================================================| DONE\n\n   Target Function: FAST LERF1\n\n-------------------------\nROTATION FUNCTION #1 OF 1\n-------------------------\n\n   Search Ensemble: model\n\n   Sampling: 5.99 degrees\n\n   SOLU SET \n   SOLU ENSEMBLE model VRMS DELTA +0.0000 RMSD 0.63 #VRMS 0.63\n\n   Spherical Harmonics\n   -------------------\n   Elmn for Data\n   Elmn Calculation for Data\n   0%                                                                          100%\n   |===========================================================================| DONE\n\n   Scanning the Range of Beta Angles\n   ---------------------------------\n   Clmn Calculation\n   0%                               100%\n   |================================| DONE\n\n   Top Peaks Without Clustering\n   Select peaks over 67.5% of top (i.e. 0.675*(top-mean)+mean)\n   There were 18 sites over 67.5% of top\n   18 peaks selected\n   The sites over 67.5% are:\n   #     Euler1 Euler2 Euler3    FSS   Z-score\n   1       16.9    1.8  341.5    100.000  8.83\n   2       77.2    1.8   14.1     96.782  8.55\n   3       28.6    3.4   61.2     96.582  8.53\n   #Sites = 18: output truncated to 3 sites\n\n   Top 18 rotations before clustering will be rescored\n   Calculating Likelihood for RF #1 of 1\n   0%                  100%\n   |===================| DONE\n\n   Mean and Standard Deviation\n   ---------------------------\n   Scoring 500 randomly sampled rotations\n   Generating Statistics for RF #1 of 1\n   0%                                                                       100%\n   |========================================================================| DONE\n\n   Highest Score (Z-score):  60.6647   (9.26)\n\n   Top Peaks With Clustering\n   Select peaks over 75% of top (i.e. 0.75*(top-mean)+mean)\n   There was 1 site over 75% of top\n   The sites over 75% are:\n   #     Euler1 Euler2 Euler3    LLG   Z-score Split #Group  FSS-this-ang/FSS-top\n   1       16.9    1.8  341.5     60.665  9.26   0.0      8    100.000/   100.000\n          106.9    1.8  341.5\n          196.9    1.8  341.5\n          286.9    1.8  341.5\n          343.1  178.2  161.5\n           73.1  178.2  161.5\n          163.1  178.2  161.5\n          253.1  178.2  161.5\n\n   Rotation Function Table: model\n   ------------------------------\n   (Z-scores from Fast Rotation Function)\n   #SET        Top    (Z)      Second    (Z)       Third    (Z)\n   1         60.66   9.26         ---    ---         ---    ---\n\n---------------\nFINAL SELECTION\n---------------\n\n   Select by Percentage of Top value: 75%\n   Top RF = 60.6647\n   Purge RF mean = -37.6886\n   Number of sets stored before final selection = 1\n   Number of solutions stored before final selection = 1\n   Number of sets stored (deleted) after final selection = 1 (0)\n   Number of solutions stored (deleted) after final selection = 1 (0)\n   Number used for purge  = 3\n\n   Rotation Function Final Selection Table\n   ---------------------------------------\n   Rotation list length by SET\n   SET#  Start Final Deleted Set (*)\n      1  1     1           -\n   ALL   1     1    \n\n------------\nOUTPUT FILES\n------------\n\n   No files output\n\nCPU Time: 0 days 0 hrs 0 mins 32.39 secs (     32.39 secs)\nFinished: Thu Oct  8 11:01:18 2020\n\n*************************************************************************************\n*** Phaser Module: MOLECULAR REPLACEMENT TRANSLATION FUNCTION               2.6.0 ***\n*************************************************************************************\n\n---------------------\nANISOTROPY CORRECTION\n---------------------\n\n   No refinement of parameters\n\n------------------------\nTRANSLATIONAL NCS VECTOR\n------------------------\n\n   Space Group :       P 41 21 2\n   Patterson Symmetry: P 4/m m m\n   Resolution of All Data (Number):        1.69  45.81 (28683)\n   Resolution of Patterson (Number):       5.00   9.93 (1112)\n   No translational ncs found or input\n\n-----------------------------\nDATA FOR TRANSLATION FUNCTION\n-----------------------------\n\n   Outliers with a probability less than 1e-06 will be rejected\n   There were 0 (0.0000%) reflections rejected\n\n   No reflections are outliers\n\n   Resolution of All Data (Number):        1.69  45.81 (28683)\n   Resolution of Selected Data (Number):   4.50  45.81 (1738)\n\n-------------------\nWILSON DISTRIBUTION\n-------------------\n\n   Parameters set for Wilson log-likelihood calculation\n   E = 0 and variance 1 for each reflection\n   Without correction for SigF to the variances,\n      Wilson log(likelihood) = - number of acentrics (1137)\n                               - half number of centrics (601/2)\n                             = -1437\n   With correction for SigF,\n      Wilson log(likelihood) = -1400.55\n\n------------------------\nALTERNATIVE SPACE GROUPS\n------------------------\n\n   Space Group(s) to be tested:\n     P 41 21 2\n\n----------\nENSEMBLING\n----------\n\n   Ensemble Generation\n   -------------------\n   Resolution of Ensembles: 4.50016\n   Ensemble        Scat% Radius Model# Rel-B Input-RMS Initial-Delta-VRMS Initial-RMS\n   model            81.2  21.50      1 -42.5     0.633              0.000       0.633\n\n---------------------\nTRANSLATION FUNCTIONS\n---------------------\n\n   Target Function: FAST LETF1\n   Sampling: 1.13 Angstroms\n\n----------------------------\nTRANSLATION FUNCTION #1 OF 1\n----------------------------\n\n   SOLU SET \n   SOLU SPAC P 41 21 2\n   SOLU TRIAL ENSEMBLE model EULER 16.917 1.830 341.488 RFZ 9.26\n   SOLU ENSEMBLE model VRMS DELTA +0.0000 RMSD 0.63 #VRMS 0.63\n\n   This set has one trial orientation\n\n   #TRIAL   Euler1 Euler2 Euler3   Ensemble\n        1     16.9    1.8  341.5   model               \n\n   Scoring 500 randomly sampled orientations and translations\n   Generating Statistics for TF SET #1 of 1\n   0% 100%\n   |==| DONE\n\n   Mean Score (Sigma):       -325.09   (36.31)\n\n   SET #1 of 1 TRIAL #1 of 1\n   -------------------------\n   Euler =   16.9    1.8  341.5, Ensemble = model\n\n   Doing Fast Translation Function FFT...\n      Done\n\n   New Top Fast Translation Function FSS = 786.88 (TFZ=20.4) at Trial #1\n\n   Top Peaks Without Clustering\n   Select peaks over 67.5% of top (i.e. 0.675*(top-mean)+mean)\n   There were 24 sites over 67.5% of top\n   24 peaks selected\n   The sites over 67.5% are:\n   #     Frac X Frac Y Frac Z    FSS   Z-score\n   1      0.972  0.987  0.002     786.88 20.41\n   2      0.974  0.985  0.923     412.03 10.41\n   3      0.973  0.984  0.158     399.73 10.08\n   #Sites = 24: output truncated to 3 sites\n\n   Top 24 translations before clustering will be rescored\n   Calculating Likelihood for TF SET #1 of 1 TRIAL #1 of 1\n   0%                        100%\n   |=========================| DONE\n\n   New Top (ML) Translation Function LLG = 506.41 (TFZ=22.9) at Trial #1\n   Top Peaks With Clustering\n   Select peaks over 75% of top (i.e. 0.75*(top-mean)+mean)\n   There were 13 sites over 75% of top\n   The sites over 75% are:\n   #     Frac X Frac Y Frac Z    LLG   Z-score Split #Group  FSS-this-xyz/FSS-top\n   1      0.972  0.987  0.002     506.41 20.41   0.0      1     786.88/    786.88\n   2      0.974  0.985  0.923      68.45 10.41  11.3      2     412.03/    412.03\n   3      0.970  0.484  0.002      67.78  9.55  28.2      1     379.88/    379.88\n   #SITES = 13: OUTPUT TRUNCATED TO 3 SITES\n\n   Translation Function Table\n   --------------------------\n   SET ROT*deep   Top   (Z)     Second   (Z)      Third   (Z) Ensemble SpaceGroup \n     1   1      506.4 20.41       68.5 10.41       67.8  9.55 model    P 41 21 2  \n   --- ---\n\n---------------\nFINAL SELECTION\n---------------\n\n   LLG will be used for purge, not FSS\n   Top TF  = 506.41\n   Top TFZ = 20.41\n   Mean TF = -325.09\n   Number used for purge  = 1\n   Cutoff for acceptance = 506.4\n      TFZ used for final selection = 10.2034\n         Number of solutions over TF final cutoff  = 0\n         Number of solutions over TFZ final cutoff = 1\n         Number of solutions over TF & TFZ cutoff  = 0\n   Number of solutions stored before final selection = 13\n   Number of solutions stored (deleted) after final selection = 1 (12)\n\n------------\nOUTPUT FILES\n------------\n\n   No files output\n\nCPU Time: 0 days 0 hrs 0 mins 37.55 secs (     37.55 secs)\nFinished: Thu Oct  8 11:01:23 2020\n\n*************************************************************************************\n*** Phaser Module: MOLECULAR REPLACEMENT PACKING ANALYSIS                   2.6.0 ***\n*************************************************************************************\n\n---------\nENSEMBLES\n---------\n\n   Packing Ensemble: model\n\n-----------------\nENSEMBLE SYMMETRY\n-----------------\n\n   Ensemble \"model\" Point Group: 1\n\n----------------------\nSTRUCTURES FOR PACKING\n----------------------\n\n   Packing will be performed with \"trace\" atoms. which are C-alphas for protein, P\n   and selected N for nucleic acid\n   If there are no trace atoms in the molecule(s) all atoms will be used in the\n   packing test\n   If the trace length exceeds 1000 atoms then the molecule(s) will be sampled on a\n   hexagonal grid and the clash distance increased in proportion to the size of the\n   hexagonal grid sampling\n   When an ensemble consists of more than one structure, the structure with the\n   highest homology is selected for packing and the structure trimmed of loops that\n   diverge more than 3A from other atoms in the ensemble\n\n   Ensemble: model\n   ---------------\n   All atoms =  1562\n   Structure with lowest rms = thau.pdb (0.63347)\n   Trace length = 207\n   Trace atoms clash if they are closer than 3.00 Angstroms\n\n----------------\nPACKING FUNCTION\n----------------\n\n   There is 1 solution to pack\n   Packing analysis\n   0% 100%\n   |==| DONE\n\n   Packing Table\n   -------------\n   Solutions accepted if total number of clashes <= 5% of trace atoms\n      i.e. total number of clashes <= 10\n   AND if number of clashes <= 5% of trace atoms for each ensemble\n      i.e. model: number of clashes <= 10\n   #in  #out Clashes Symm TF-SET  ROT TFpk#        TF    TFZ    SpaceGroup \n   1    Top1  0      NO       1     1    1        506.41 20.41  P 41 21 2  \n\n   1 accepted of 1 solutions\n\n------------\nOUTPUT FILES\n------------\n\n   No files output\n\nCPU Time: 0 days 0 hrs 0 mins 37.61 secs (     37.61 secs)\nFinished: Thu Oct  8 11:01:23 2020\n\n*************************************************************************************\n*** Phaser Module: MOLECULAR REPLACEMENT REFINEMENT AND PHASING             2.6.0 ***\n*************************************************************************************\n\n---------------------\nANISOTROPY CORRECTION\n---------------------\n\n   No refinement of parameters\n\n------------------------\nTRANSLATIONAL NCS VECTOR\n------------------------\n\n   Space Group :       P 41 21 2\n   Patterson Symmetry: P 4/m m m\n   Resolution of All Data (Number):        1.69  45.81 (28683)\n   Resolution of Patterson (Number):       5.00   9.93 (1112)\n   No translational ncs found or input\n\n-------------------------------\nDATA FOR REFINEMENT AND PHASING\n-------------------------------\n\n   Outliers with a probability less than 1e-06 will be rejected\n   There were 0 (0.0000%) reflections rejected\n\n   No reflections are outliers\n\n   Resolution of All Data (Number):        1.69  45.81 (28683)\n   Resolution of Selected Data (Number):   4.50  45.81 (1738)\n\n-------------------\nWILSON DISTRIBUTION\n-------------------\n\n   Parameters set for Wilson log-likelihood calculation\n   E = 0 and variance 1 for each reflection\n   Without correction for SigF to the variances,\n      Wilson log(likelihood) = - number of acentrics (1137)\n                               - half number of centrics (601/2)\n                             = -1437\n   With correction for SigF,\n      Wilson log(likelihood) = -1400.55\n\n----------\nENSEMBLING\n----------\n\n   Ensemble Generation\n   -------------------\n   Resolution of Ensembles: 4.50016\n   Ensemble        Scat% Radius Model# Rel-B Input-RMS Initial-Delta-VRMS Initial-RMS\n   model            81.2  21.50      1 -42.5     0.633              0.000       0.633\n\n----------\nREFINEMENT\n----------\n\n   Protocol cycle #1 of 1\n   Refinement protocol for this macrocycle:\n   ROTATION      : REFINE\n   TRANSLATION   : REFINE\n   BFACTOR       : REFINE\n   MODEL VRMS    : FIX\n   MAP CELL SCALE: FIX\n   MAP OFACTOR   : FIX\n   LAST ONLY     : FALSE\n\n   There is 1 solution to refine\n   Refining solutions\n   0% 100%\n   |==| DONE\n\n\n   REFINING SET # 1 OF 1\n   ---------------------\n   Initial Parameters:\n   SOLU SET \n   SOLU 6DIM ENSE model EULER 286.9 1.8 341.5 FRAC -0.51 0.53 -0.25 BFAC 0.00\n   SOLU ENSEMBLE model VRMS DELTA +0.0000 RMSD 0.63 #VRMS 0.63\n\n   Performing Minimization...\n      Done\n   --- Convergence before iteration limit (50) at cycle 11 ---\n   Start-this-macrocycle End-this-macrocycle Change-this-macrocycle\n         507.681               571.644                63.963\n\n   Final Parameters:\n   SOLU SET \n   SOLU 6DIM ENSE model EULER 313.6 0.6 315.5 FRAC -0.52 0.51 -0.25 BFAC -1.19\n   SOLU ENSEMBLE model VRMS DELTA +0.0000 RMSD 0.63 #VRMS 0.63\n\n---------------\nTFZ EQUIVALENTS\n---------------\n\n   Refined TFZ equivalents calculated\n   1 top TFZ equivalents calculated\n      1 (Topfiles)\n      0 with TFZ > 6 (TFZ for Possibly Solved)\n\n   TFZ equivalent calculation for top solution #1 of 1\n   ---------------------------------------------------\n      Solution #1 of 1\n\n   Generating Statistics\n   0%                                                                       100%\n   |========================================================================| DONE\n\n   Mean Score (Sigma):       -346.80   (39.28)\n   Refined TF/TFZ equivalent = 570.88/23.4 (Unrefined TF/TFZ=506.41/20.4)\n\n   Mean and Sigma after Refinement (for Purge)\n   -------------------------------------------\n   Scoring 500 randomly sampled orientations and translations\n\n   Generating Statistics\n   0% 100%\n   |==| DONE\n\n   Mean Score for Purge before Refinement:  -325.09\n   Mean Score for Purge after Refinement :  -346.80\n\n---------------\nFIND DUPLICATES\n---------------\n\n   Check for nearly equivalent solutions\n   Calculating Duplicates for 1 solutions\n   0% 100%\n   |==| DONE\n\n   No duplicate solutions found\n\n---------------------\nFIND TEMPLATE MATCHES\n---------------------\n\n   No Template Solution(s) for comparison\n\n---------------\nPURGE SELECTION\n---------------\n\n   Purge solutions according to highest LLG from Refinement\n   --------------------------------------------------------\n   Top LLG = 570.88\n   Mean LLG = -346.8\n   Percent used for purge = 75%\n      Cutoff for acceptance = 341.5\n   Number used for purge  = 1\n      Cutoff for acceptance = 570.9\n   Overall cutoff for acceptance (excluding high TFZ) = 570.9\n   Number of solutions stored before purge = 1\n   Number of solutions stored (deleted) after purge = 1 (0)\n\n-------\nRESULTS\n-------\n\n   Refinement Table (Sorted)\n   -------------------------\n   #out =#out #in =T (Start LLG Rval TFZ) (Refined LLG Rval TFZ==) SpaceGroup  Cntrst\n   Top1 ---   1           506.4 36.1 20.4        570.9 34.5 23.4   P 41 21 2     n/a \n\n   Refinement Table (Variance Ranges)\n   ----------------------------------\n   Range of delta-VRMS and VRMS given over current solution list (1 solution(s))\n   Ensemble        Model#   RMS   Delta-VRMS min/max  (VRMS min/max)\n   model                1   0.633   +0.000/+0.000    ( 0.633/ 0.633 )\n\n------------\nOUTPUT FILES\n------------\n\n   A sharpening B-factor of 100% of the isotropic B-factor in the direction of\n   smallest falloff (i.e. highest resolution) has been added to the anisotropically\n   corrected structure factors (FWT,DELFWT)\n\n   Calculation of Map Coefficients\n   -------------------------------\n   1 top map coefficients calculated\n\n   Map coefficient calculated for top solution #1\n   SOLU SPAC P 41 21 2\n   SOLU 6DIM ENSE model EULER 313.6 0.6 315.5 FRAC -0.52 0.51 -0.25 BFAC -1.19\n   SOLU ENSEMBLE model VRMS DELTA +0.0000 RMSD 0.63 #VRMS 0.63\n\n   No files output\n\nCPU Time: 0 days 0 hrs 0 mins 44.39 secs (     44.39 secs)\nFinished: Thu Oct  8 11:01:30 2020\n\n*************************************************************************************\n*** Phaser Module: AUTOMATED MOLECULAR REPLACEMENT                          2.6.0 ***\n*************************************************************************************\n\n*** Current is Best Solution (first search)\n*** Current solution has 1 component\n*** New Best LLG = 570.9 (resolution = 4.50)\n*** Best Component so far = model \n\nCPU Time: 0 days 0 hrs 0 mins 44.40 secs (     44.40 secs)\nFinished: Thu Oct  8 11:01:30 2020\n\n*************************************************************************************\n*** Phaser Module: AUTOMATED MOLECULAR REPLACEMENT                          2.6.0 ***\n*************************************************************************************\n\n*** Solutions will be refined to highest resolution\n\nCPU Time: 0 days 0 hrs 0 mins 45.72 secs (     45.72 secs)\nFinished: Thu Oct  8 11:01:31 2020\n\n*************************************************************************************\n*** Phaser Module: MOLECULAR REPLACEMENT REFINEMENT AND PHASING             2.6.0 ***\n*************************************************************************************\n\n---------------------\nANISOTROPY CORRECTION\n---------------------\n\n   No refinement of parameters\n\n------------------------\nTRANSLATIONAL NCS VECTOR\n------------------------\n\n   Space Group :       P 41 21 2\n   Patterson Symmetry: P 4/m m m\n   Resolution of All Data (Number):        1.69  45.81 (28683)\n   Resolution of Patterson (Number):       5.00   9.93 (1112)\n   No translational ncs found or input\n\n-------------------------------\nDATA FOR REFINEMENT AND PHASING\n-------------------------------\n\n   Outliers with a probability less than 1e-06 will be rejected\n   There were 0 (0.0000%) reflections rejected\n\n   No reflections are outliers\n\n   Resolution of All Data (Number):        1.69  45.81 (28683)\n   Resolution of Selected Data (Number):   1.69  45.81 (28683)\n\n-------------------\nWILSON DISTRIBUTION\n-------------------\n\n   Parameters set for Wilson log-likelihood calculation\n   E = 0 and variance 1 for each reflection\n   Without correction for SigF to the variances,\n      Wilson log(likelihood) = - number of acentrics (24422)\n                               - half number of centrics (4261/2)\n                             = -26552\n   With correction for SigF,\n      Wilson log(likelihood) = -27040.4\n\n----------\nENSEMBLING\n----------\n\n   Ensemble Generation: model\n   --------------------------\n   Ensemble configured for structure factor interpolation\n   Ensemble configured to resolution 1.69\n   PDB file # 1: thau.pdb\n      This pdb file contains 1 model\n      The input RmsD of model #1 with respect to the real structure is 0.63\n\n   Electron Density Calculation\n   0%      100%\n   |=======| DONE\n\n   Weighting Structure Factors\n   0%                                                                       100%\n   |========================================================================| DONE\n\n   VRMS delta lower/upper limit = -0.389990 / 12.688216\n      RMSD upper limit(s): 3.62\n      RMSD lower limit(s): 0.11\n\n   Ensemble Generation\n   -------------------\n   Resolution of Ensembles: 1.68633\n   Ensemble        Scat% Radius Model# Rel-B Input-RMS Initial-Delta-VRMS Initial-RMS\n   model            81.2  21.50      1  24.0     0.633              0.000       0.633\n\n----------\nREFINEMENT\n----------\n\n   Protocol cycle #1 of 1\n   Refinement protocol for this macrocycle:\n   ROTATION      : REFINE\n   TRANSLATION   : REFINE\n   BFACTOR       : REFINE\n   MODEL VRMS    : REFINE\n   MAP CELL SCALE: FIX\n   MAP OFACTOR   : FIX\n   LAST ONLY     : FALSE\n\n   There is 1 solution to refine\n   Refining solutions\n   0% 100%\n   |==| DONE\n\n\n   REFINING SET # 1 OF 1\n   ---------------------\n   Initial Parameters:\n   SOLU SET \n   SOLU 6DIM ENSE model EULER 313.6 0.6 315.5 FRAC -0.52 0.51 -0.25 BFAC -1.19\n   SOLU ENSEMBLE model VRMS DELTA +0.0000 RMSD 0.63 #VRMS 0.63\n\n   Performing Minimization...\n      Done\n   --- Convergence before iteration limit (50) at cycle 8 ---\n   Start-this-macrocycle End-this-macrocycle Change-this-macrocycle\n        5015.298              9297.113              4281.816\n\n   Final Parameters:\n   SOLU SET \n   SOLU 6DIM ENSE model EULER 310.4 0.7 318.7 FRAC -0.52 0.51 -0.25 BFAC -1.19\n   SOLU ENSEMBLE model VRMS DELTA -0.3227 RMSD 0.63 #VRMS 0.28\n\n---------------\nTFZ EQUIVALENTS\n---------------\n\n   Refined TFZ equivalents calculated\n   1 top TFZ equivalents calculated\n      1 (Topfiles)\n      0 with TFZ > 6 (TFZ for Possibly Solved)\n\n   TFZ equivalent calculation for top solution #1 of 1\n   ---------------------------------------------------\n      Solution #1 of 1\n\n   Generating Statistics\n   0%                                                                       100%\n   |========================================================================| DONE\n\n   Mean Score (Sigma):       -14187.35   (247.03)\n   Refined TF/TFZ equivalent = 9294.31/95.1 (Unrefined TF/TFZ=5014.76/23.4)\n\n   Mean and Sigma after Refinement (for Purge)\n   -------------------------------------------\n   Scoring 500 randomly sampled orientations and translations\n\n   Generating Statistics\n   0% 100%\n   |==| DONE\n\n   Mean Score for Purge before Refinement:  -346.80\n   Mean Score for Purge after Refinement :  -14187.35\n\n---------------\nFIND DUPLICATES\n---------------\n\n   Check for nearly equivalent solutions\n   Calculating Duplicates for 1 solutions\n   0% 100%\n   |==| DONE\n\n   No duplicate solutions found\n\n---------------------\nFIND TEMPLATE MATCHES\n---------------------\n\n   No Template Solution(s) for comparison\n\n---------------\nPURGE SELECTION\n---------------\n\n   Purge solutions according to highest LLG from Refinement\n   --------------------------------------------------------\n   Top LLG = 9294.31\n   Mean LLG = -14187.4\n   Percent used for purge = 75%\n      Cutoff for acceptance = 3423.9\n   Number used for purge  = 1\n      Cutoff for acceptance = 9294.3\n   Overall cutoff for acceptance (excluding high TFZ) = 9294.3\n   Number of solutions stored before purge = 1\n   Number of solutions stored (deleted) after purge = 1 (0)\n\n-------\nRESULTS\n-------\n\n   Refinement Table (Sorted)\n   -------------------------\n   Refinement to full resolution\n   #out =#out #in =T (Start LLG Rval TFZ) (Refined LLG Rval TFZ==) SpaceGroup  Cntrst\n   Top1 ---   1          5014.8 34.0 23.4       9294.3 33.6 95.1   P 41 21 2     n/a \n\n   Refinement Table (Variance Ranges)\n   ----------------------------------\n   Range of delta-VRMS and VRMS given over current solution list (1 solution(s))\n   Ensemble        Model#   RMS   Delta-VRMS min/max  (VRMS min/max)\n   model                1   0.633   -0.323/-0.323    ( 0.280/ 0.280 )\n\n------------\nOUTPUT FILES\n------------\n\n   A sharpening B-factor of 100% of the isotropic B-factor in the direction of\n   smallest falloff (i.e. highest resolution) has been added to the anisotropically\n   corrected structure factors (FWT,DELFWT)\n\n   Calculation of Map Coefficients\n   -------------------------------\n   1 top map coefficients calculated\n\n   Map coefficient calculated for top solution #1\n   SOLU SPAC P 41 21 2\n   SOLU 6DIM ENSE model EULER 310.4 0.7 318.7 FRAC -0.52 0.51 -0.25 BFAC -1.19\n   SOLU ENSEMBLE model VRMS DELTA -0.3227 RMSD 0.63 #VRMS 0.28\n\n   No files output\n\nCPU Time: 0 days 0 hrs 1 mins 59.00 secs (    119.00 secs)\nFinished: Thu Oct  8 11:02:44 2020\n\n*************************************************************************************\n*** Phaser Module: AUTOMATED MOLECULAR REPLACEMENT                          2.6.0 ***\n*************************************************************************************\n\n*** SINGLE solution\n\n*** Solution written to PDB file:  P41212_all_0.1.pdb\n*** Solution written to MTZ file:  P41212_all_0.1.mtz\n*** Solution annotation (history):\n   SOLU SET  RFZ=9.3 TFZ=20.4 PAK=0 LLG=571 TFZ==23.4 LLG=9294 TFZ==95.1\n   SOLU SPAC P 41 21 2\n   SOLU 6DIM ENSE model EULER 310.4 0.7 318.7 FRAC -0.52 0.51 -0.25 BFAC -1.19\n   SOLU ENSEMBLE model VRMS DELTA -0.3227 RMSD 0.63 #VRMS 0.28\n\nCPU Time: 0 days 0 hrs 1 mins 59.03 secs (    119.03 secs)\nFinished: Thu Oct  8 11:02:45 2020\n\n\n--------------------\nEXIT STATUS: SUCCESS\n--------------------\n\nCPU Time: 0 days 0 hrs 1 mins 59.03 secs (    119.03 secs)\nFinished: Thu Oct  8 11:02:45 2020\n\n</pre>\n</html>\n"}, 
              "clash": 0.0, "tNCS": False, "gain": 9294.313971709074, "tfz": 20.4, "ID": "P41212_all_0", 
              "map_1_1": {"path": "/gpfs6/users/necat/Jon/RAPD_test/Output/Phaser_test/rapd_mr_thau_free/P41212_all_0/P41212_all_0.1_mFo-DFc.ccp4.tar.bz2", "hash": "c2594b70b41b0f7e58e0ba3f97b7e46e7fcf8517", "description": "map_1_1"}, 
              "mtz": {"path": "/gpfs6/users/necat/Jon/RAPD_test/Output/Phaser_test/rapd_mr_thau_free/P41212_all_0/P41212_all_0.1.mtz.tar.bz2", "hash": "d0ed3936ee117516f136ceadf66ce42f4dc604ab", "description": "mtz"}, 
              "mtz_file": "/gpfs6/users/necat/Jon/RAPD_test/Output/Phaser_test/rapd_mr_thau_free/P41212_all_0/P41212_all_0.1.mtz", 
              "tar": {"path": "/gpfs6/users/necat/Jon/RAPD_test/Output/Phaser_test/rapd_mr_thau_free/P41212_all_0/P41212_all_0.tar.bz2", "hash": "b567193c5eeb3eec71e762b779b1d9770ab85621", "description": "P41212_all_0_files"}, 
              "nmol": 1, "rfz": 9.3, 
              "map_2_1": {"path": "/gpfs6/users/necat/Jon/RAPD_test/Output/Phaser_test/rapd_mr_thau_free/P41212_all_0/P41212_all_0.1_2mFo-DFc.ccp4.tar.bz2", "hash": "c186bde77a05bf600ffbe0f2bdb0fb2c0d8144f5", "description": "map_2_1"}, 
              "solution": True, "adf": None, "spacegroup": "P41212", 
              "pdb": {"path": "/gpfs6/users/necat/Jon/RAPD_test/Output/Phaser_test/rapd_mr_thau_free/P41212_all_0/P41212_all_0.1.pdb.tar.bz2", "hash": "39312381fd225d35b846c8b6c906ef8648801e6e", "description": "pdb"}, 
              "dir": "/gpfs6/users/necat/Jon/RAPD_test/Output/Phaser_test/rapd_mr_thau_free/P41212_all_0", "peak": None}

int_input = {u'preferences': {u'exchange_dir': u'/gpfs6/users/necat/rapd2/exchange_dir', 
                              u'xdsinp': [[u'CLUSTER_RADIUS', u'2'], [u'DETECTOR', u'EIGER'], [u'DIRECTION_OF_DETECTOR_X-AXIS', u'1 0 0'], [u'DIRECTION_OF_DETECTOR_Y-AXIS', u'0 1 0'], [u'FRACTION_OF_POLARIZATION', u'0.99'], [u'INCIDENT_BEAM_DIRECTION', u'0 0 1'], [u'INCLUDE_RESOLUTION_RANGE', u'200.0 0.0'], [u'MAX_CELL_ANGLE_ERROR', u'2.0'], [u'MAX_CELL_AXIS_ERROR', u'0.03'], [u'MAX_FAC_Rmeas', u'2.0'], [u'MINIMUM_NUMBER_OF_PIXELS_IN_A_SPOT', u'4'], [u'MINIMUM_VALID_PIXEL_VALUE', u'0'], [u'MIN_RFL_Rmeas', u' 50'], [u'NUMBER_OF_PROFILE_GRID_POINTS_ALONG_ALPHA/BETA', u'13'], [u'NUMBER_OF_PROFILE_GRID_POINTS_ALONG_GAMMA', u'9'], [u'NX', u'4150'], [u'NY', u'4371'], [u'OVERLOAD', u'3000000'], [u'POLARIZATION_PLANE_NORMAL', u'0 1 0'], [u'QX', u'0.075'], [u'QY', u'0.075'], [u'REFINE(CORRECT)', u'POSITION DISTANCE BEAM ORIENTATION CELL AXIS'], [u'REFINE(IDXREF)', u'BEAM AXIS ORIENTATION CELL'], [u'REFINE(INTEGRATE)', u'BEAM ORIENTATION CELL! POSITION'], [u'ROTATION_AXIS', u'1 0 0'], [u'SENSOR_THICKNESS', u'0.32'], [u'SEPMIN', u'4'], [u'TEST_RESOLUTION_RANGE', u'8.0 4.5'], [u'TRUSTED_REGION', u'0.00 1.2'], [u'UNTRUSTED_RECTANGLE1', u' 1030 1041      0 4372'], [u'UNTRUSTED_RECTANGLE10', u'    0 4151   3820 3858'], [u'UNTRUSTED_RECTANGLE2', u' 2070 2081      0 4372'], [u'UNTRUSTED_RECTANGLE3', u' 3110 3121      0 4372'], [u'UNTRUSTED_RECTANGLE4', u'    0 4151    514  552'], [u'UNTRUSTED_RECTANGLE5', u'    0 4151   1065 1103'], [u'UNTRUSTED_RECTANGLE6', u'    0 4151   1616 1654'], [u'UNTRUSTED_RECTANGLE7', u'    0 4151   2167 2205'], [u'UNTRUSTED_RECTANGLE8', u'    0 4151   2718 2756'], [u'UNTRUSTED_RECTANGLE9', u'    0 4151   3269 3307'], [u'VALUE_RANGE_FOR_TRUSTED_DETECTOR_PIXELS', u'8000. 30000.'], [u'UNTRUSTED_RECTANGLE11', u'    0 4151    225  260'], [u'UNTRUSTED_RECTANGLE12', u'    0 4151    806  811'], [u'UNTRUSTED_RECTANGLE13', u'    0 4151   1357 1362'], [u'UNTRUSTED_RECTANGLE14', u'    0 4151   1908 1913'], [u'UNTRUSTED_RECTANGLE15', u'    0 4151   2459 2464'], [u'UNTRUSTED_RECTANGLE16', u'    0 4151   3010 3015'], [u'UNTRUSTED_RECTANGLE17', u'    0 4151   3561 3566'], [u'UNTRUSTED_RECTANGLE18', u'    0 4151   4112 4117'], [u'CLUSTER_NODES', u'general.q']], 
                              u'analysis': True, u'json': False, u'cleanup': False, u'run_mode': u'server'}, 
             u'process': {u'status': 0, u'parent_id': False, u'result_id': u'5f85df03f46833117fb04f63', u'run_id': ObjectId('5f85df00f46833117fb04f61'), u'session_id': u'5f85c10725c6336ee811c982', u'image_id': u'5f85df03f46833117fb04f62', u'type': u'plugin'}, 
             u'directories': {u'data_root_dir': u'/gpfs2/users/upenn/sriram_E_5366', u'work': u'/gpfs6/users/necat/rapd2/integrate/2020-10-13/dg9lite_px125b2', u'launch_dir': u'/gpfs6/users/necat/rapd2', u'plugin_directories': [u'sites.plugins', u'plugins']}, 
             u'command': u'INTEGRATE', 
             u'data': {u'image_data': {u'tau': None, u'run_id': u'5f85df00f46833117fb04f61', u'period': 0.2, u'place_in_run': 1, u'rapd_detector_id': u'necat_dectris_eiger16m', u'sample_mounter_position': u'E16', u'excluded_pixels': None, u'threshold': 6331.0, u'osc_start': 62.0, u'axis': u'omega', u'image_prefix': u'dg9lite_px125b2', u'size1': 4150, u'size2': 4371, u'osc_range': 0.2, u'site_tag': u'NECAT_E', u'beam_x': 2059.07, u'sensor_thickness': 0.45, u'detector': u'Eiger-16M', u'count_cutoff': 502255, u'trim_file': None, u'md2_aperture': 0.05, u'n_excluded_pixels': 1198784, u'x_beam_size': 0.05, u'data_root_dir': u'/gpfs2/users/upenn/sriram_E_5366', u'y_beam_size': 0.02, u'twotheta': 0.0, u'directory': u'/epu/rdma/gpfs2/users/upenn/sriram_E_5366/images/Kay/runs/dg9lite_px125b2/dg9lite_px125b2_1_000001', u'beam_y': 2193.33, u'wavelength': 0.97918, u'gain': None, u'date': u'2020-10-13T12:08:18.212958', u'run_number_in_template': True, u'detector_sn': u'E-32-0108', u'pixel_size': 0.075, u'y_beam': 154.43025, u'distance': 400.0, u'run_number': 1, u'image_template': u'dg9lite_px125b2_1_??????.cbf', u'transmission': 5.2, u'collect_mode': u'RUN', u'flat_field': None, u'flux': 260000000000, u'time': 0.199995, u'x_beam': 164.49974999999998, u'fullname': u'/epu/rdma/gpfs2/users/upenn/sriram_E_5366/images/Kay/runs/dg9lite_px125b2/dg9lite_px125b2_1_000001/dg9lite_px125b2_1_000001.cbf', u'_id': u'5f85df03f46833117fb04f62', u'ring_current': 101.5, u'image_number': 1}, 
                      # u'run_data': {u'start_image_number': 1, u'run_id': u'5f85df00f46833117fb04f61', u'energy': 12662.0, u'osc_start': 62.0, u'number_images': 400, u'image_prefix': u'dg9lite_px125b2', u'image_template': u'dg9lite_px125b2_1_??????.cbf', u'site_tag': u'NECAT_E', u'beamline': u'NECAT_E', u'phi': 0.0, u'distance': 400.0, u'timestamp': datetime.datetime(2020, 10, 13, 17, 8, 16, 223000, tzinfo=<bson.tz_util.FixedOffset object at 0x2b47d61bd9d0>), u'twotheta': None, u'osc_axis': u'phi', u'omega': None, u'osc_width': 0.2, u'run_number': 1, u'kappa': None, u'transmission': 5.0, u'anomalous': None, u'time': 0.2, u'directory': u'/epu/rdma/gpfs2/users/upenn/sriram_E_5366/images/Kay/runs/dg9lite_px125b2/dg9lite_px125b2_1_000001', u'_id': ObjectId('5f85df00f46833117fb04f61')}
                       },
              u'site_parameters': {u'DETECTOR_DISTANCE_MAX': 1000.0, u'BEAM_CENTER_Y': [155.04591768967472, -0.002128702601888507, 1.6853682723685666e-06, -6.043716204571221e-10], u'BEAM_APERTURE_SHAPE': u'circle', u'DETECTOR_DISTANCE_MIN': 150.0, u'BEAM_CENTER_DATE': u'2020-02-04', u'DIFFRACTOMETER_OSC_MIN': 0.05, u'BEAM_CENTER_X': [165.1427628756774, -0.0014361166886983285, -1.728236304090641e-06, 3.2731939791152326e-09], u'BEAM_SIZE_Y': 0.02, u'BEAM_SIZE_X': 0.05, u'DETECTOR_TIME_MIN': 0.05, u'BEAM_FLUX': 5000000000000.0, u'BEAM_SHAPE': u'ellipse'}
              }

image_data = {u'tau': None, u'run_id': u'5f85df00f46833117fb04f61', u'period': 0.2, u'place_in_run': 1, u'rapd_detector_id': u'necat_dectris_eiger16m', u'sample_mounter_position': u'E16', u'excluded_pixels': None, u'threshold': 6331.0, u'osc_start': 62.0, u'axis': u'omega', u'image_prefix': u'dg9lite_px125b2', u'size1': 4150, u'size2': 4371, u'osc_range': 0.2, u'site_tag': u'NECAT_E', u'beam_x': 2059.07, u'sensor_thickness': 0.45, u'detector': u'Eiger-16M', u'count_cutoff': 502255, u'trim_file': None, u'md2_aperture': 0.05, u'n_excluded_pixels': 1198784, u'x_beam_size': 0.05, u'data_root_dir': u'/gpfs2/users/upenn/sriram_E_5366', u'y_beam_size': 0.02, u'twotheta': 0.0, u'directory': u'/epu/rdma/gpfs2/users/upenn/sriram_E_5366/images/Kay/runs/dg9lite_px125b2/dg9lite_px125b2_1_000001', u'beam_y': 2193.33, u'wavelength': 0.97918, u'gain': None, u'date': u'2020-10-13T12:08:18.212958', u'run_number_in_template': True, u'detector_sn': u'E-32-0108', u'pixel_size': 0.075, u'y_beam': 154.43025, u'distance': 400.0, u'run_number': 1, u'image_template': u'dg9lite_px125b2_1_??????.cbf', u'transmission': 5.2, u'collect_mode': u'RUN', u'flat_field': None, u'flux': 260000000000, u'time': 0.199995, u'x_beam': 164.49974999999998, u'fullname': u'/epu/rdma/gpfs2/users/upenn/sriram_E_5366/images/Kay/runs/dg9lite_px125b2/dg9lite_px125b2_1_000001/dg9lite_px125b2_1_000001.cbf', u'_id': u'5f85df03f46833117fb04f62', u'ring_current': 101.5, u'image_number': 1}
"""
#log_path = "/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_mr.log"
#dir, log_name = os.path.split(log_path)
#print log_name[:log_name.rfind(".")]

#results_json = None
#red = connect_remote_redis()
#results_json = redis.get('Phaser_3428')



#redis.setex(tag, 86400, json.dumps(phaser_result))
#phaser_results = {"logs": {"phaser": "*************************************************************************************\n*** Phaser Module: AUTOMATED MOLECULAR REPLACEMENT                          2.6.0 ***\n*************************************************************************************\n\n*** Steps:\n***    Cell Content Analysis\n***    Anisotropy correction\n***    Translational NCS correction\n***    Rotation Function\n***    Translation Function\n***    Packing\n***    Refinement\n***    Final Refinement (if data higher resolution than search resolution)\n*** Number of search ensembles = 2\n*** Search Method: FAST\n*** Input Search Order:\n*** #1   model  \n*** #2   model  \n*** Automatic (best predicted) search order WILL be used\n\nCPU Time: 0 days 0 hrs 0 mins 0.18 secs (      0.18 secs)\nFinished: Wed Oct 14 14:54:40 2020\n\n*************************************************************************************\n*** Phaser Module: CELL CONTENT ANALYSIS                                    2.6.0 ***\n*************************************************************************************\n\n   Space-Group Name (Hall Symbol): P 2 2 2 ( P 2 2)\n   Space-Group Number: 16\n   Unit Cell:   57.87   68.12  235.95   90.00   90.00   90.00\n\n--------------------\nSPACE GROUP ANALYSIS\n--------------------\n\n   Input Space Group: P 2 2 2\n\n   (a) Space groups derived by translation (screw) symmetry\n   --------------------------------------------------------\n   Z   Space Group          Hall Symbol                   \n   ----\n   4   P 2 2 2               P 2 2                        \n       P 2 2 21              P 2c 2                       \n       P 21 2 2              P 2c 2 (z,x,y)               \n       P 2 21 2              P 2c 2 (y,z,x)               \n       P 21 21 2             P 2 2ab                      \n       P 2 21 21             P 2 2ab (z,x,y)              \n       P 21 2 21             P 2 2ab (y,z,x)              \n       P 21 21 21            P 2ac 2ab                    \n   ----\n\n   (b) Subgroups of (a) for perfect twinning expansions\n   ----------------------------------------------------\n   Z   Space Group          Hall Symbol                   \n   ----\n   1   P 1                   P 1                          \n   ---\n   2   P 1 2 1               P 2y                         \n       P 1 1 2               P 2y (z,x,y)                 \n       P 2 1 1               P 2y (y,z,x)                 \n       P 1 21 1              P 2yb                        \n       P 1 1 21              P 2yb (z,x,y)                \n       P 21 1 1              P 2yb (y,z,x)                \n   ----\n\n   Total Scattering = 326650\n   MW of \"average\" protein to which Matthews applies: 100175\n   Resolution for Matthews calculation:  3.12\n\n   Z       MW         VM    % solvent  rel. freq.\n   1       100175     2.32  47.01      1.000       <== most probable\n\n   Z is the number of multiples of the total composition\n   In most cases the most probable Z value should be 1\n   If it is not 1, you may need to consider other compositions\n\n   Histogram of relative frequencies of VM values\n   ----------------------------------------------\n   Frequency of most common VM value normalized to 1\n   VM values plotted in increments of 1/VM (0.02)\n\n        <--- relative frequency --->\n        0.0  0.1  0.2  0.3  0.4  0.5  0.6  0.7  0.8  0.9  1.0  \n        |    |    |    |    |    |    |    |    |    |    |    \n   10.00 -\n    8.33 -\n    7.14 -\n    6.25 -\n    5.56 -\n    5.00 -\n    4.55 --\n    4.17 ---\n    3.85 -----\n    3.57 --------\n    3.33 -------------\n    3.12 -------------------\n    2.94 --------------------------\n    2.78 ----------------------------------\n    2.63 ------------------------------------------\n    2.50 ------------------------------------------------\n    2.38 --------------------------------------------------\n    2.27 *********************************************** (COMPOSITION*1)\n    2.17 ---------------------------------------\n    2.08 ----------------------------\n    2.00 -----------------\n    1.92 ---------\n    1.85 ----\n    1.79 --\n    1.72 -\n    1.67 -\n    1.61 -\n    1.56 -\n    1.52 -\n    1.47 -\n    1.43 -\n    1.39 -\n    1.35 -\n    1.32 -\n    1.28 -\n    1.25 -\n\n   Most probable VM for resolution = 2.38756\n   Most probable MW of protein in asu for resolution = 97389.3\n\nCPU Time: 0 days 0 hrs 0 mins 0.25 secs (      0.25 secs)\nFinished: Wed Oct 14 14:54:40 2020\n\n*************************************************************************************\n*** Phaser Module: AUTOMATED MOLECULAR REPLACEMENT                          2.6.0 ***\n*************************************************************************************\n\n   Composition Table\n   -----------------\n   Total Scattering = 326650\n   Search occupancy factor = 1 (default)\n   Ensemble                        Frac.Scat.  (Search Frac.Scat.)\n   \"model\"                           44.16%          44.16%\n\nCPU Time: 0 days 0 hrs 0 mins 0.25 secs (      0.25 secs)\nFinished: Wed Oct 14 14:54:40 2020\n\n*************************************************************************************\n*** Phaser Module: ANISOTROPY CORRECTION                                    2.6.0 ***\n*************************************************************************************\n\n------------------------------\nDATA FOR ANISOTROPY CORRECTION\n------------------------------\n\n   Resolution of All Data (Number):        3.12 117.97 (17283)\n   Resolution of Selected Data (Number):   3.12 117.97 (17283)\n\n---------------------\nANISOTROPY CORRECTION\n---------------------\n\n   Protocol cycle #1 of 3\n   Refinement protocol for this macrocycle:\n   BIN SCALES: REFINE\n   ANISOTROPY: REFINE\n   SOLVENT K:  FIX\n   SOLVENT B:  FIX\n\n   Protocol cycle #2 of 3\n   Refinement protocol for this macrocycle:\n   BIN SCALES: REFINE\n   ANISOTROPY: REFINE\n   SOLVENT K:  FIX\n   SOLVENT B:  FIX\n\n   Protocol cycle #3 of 3\n   Refinement protocol for this macrocycle:\n   BIN SCALES: REFINE\n   ANISOTROPY: REFINE\n   SOLVENT K:  FIX\n   SOLVENT B:  FIX\n\n   Outliers with a probability less than 1e-06 will be rejected\n   There were 0 (0.0000%) reflections rejected\n\n   No reflections are outliers\n\n   Performing Minimization...\n      Done\n   --- Convergence before iteration limit (50) at cycle 10 ---\n   Start-this-macrocycle End-this-macrocycle Change-this-macrocycle\n     -200553.504           -199628.420               925.084\n\n   Principal components of anisotropic part of B affecting observed amplitudes:\n     eigenB (A^2)     direction cosines (orthogonal coordinates)\n        25.305              1.0000  -0.0000  -0.0000\n       -12.142              0.0000   0.0000   1.0000\n       -13.163              0.0000   1.0000  -0.0000\n   Anisotropic deltaB (i.e. range of principal components):  38.468\n   Resharpening B (to restore strong direction of diffraction): -13.163\n   Wilson scale applied to get observed intensities: 4.1425e-01\n\n   Outliers with a probability less than 1e-06 will be rejected\n   There were 1 (0.0058%) reflections rejected\n\n      H    K    L   reso     Eo^2    sigma     probability\n      7    9   20   5.05   15.998    0.628       1.672e-07\n\n   Performing Minimization...\n      Done\n   --- Convergence before iteration limit (50) at cycle 2 ---\n   Start-this-macrocycle End-this-macrocycle Change-this-macrocycle\n     -199601.394           -199601.155                 0.239\n\n   Principal components of anisotropic part of B affecting observed amplitudes:\n     eigenB (A^2)     direction cosines (orthogonal coordinates)\n        25.329              1.0000  -0.0000  -0.0000\n       -12.174              0.0000   0.0000   1.0000\n       -13.155              0.0000   1.0000  -0.0000\n   Anisotropic deltaB (i.e. range of principal components):  38.484\n   Resharpening B (to restore strong direction of diffraction): -13.155\n   Wilson scale applied to get observed intensities: 4.1357e-01\n\n   Outliers with a probability less than 1e-06 will be rejected\n   There were 1 (0.0058%) reflections rejected\n\n      H    K    L   reso     Eo^2    sigma     probability\n      7    9   20   5.05   16.529    0.648       1.010e-07\n\n   Performing Minimization...\n      Done\n   --- Convergence before iteration limit (50) at cycle 1 ---\n   Start-this-macrocycle End-this-macrocycle Change-this-macrocycle\n     -199601.155           -199601.155                 0.000\n\n   Principal components of anisotropic part of B affecting observed amplitudes:\n     eigenB (A^2)     direction cosines (orthogonal coordinates)\n        25.329              1.0000  -0.0000  -0.0000\n       -12.174              0.0000   0.0000   1.0000\n       -13.155              0.0000   1.0000  -0.0000\n   Anisotropic deltaB (i.e. range of principal components):  38.484\n   Resharpening B (to restore strong direction of diffraction): -13.155\n   Wilson scale applied to get observed intensities: 4.1357e-01\n\n   Refined Anisotropy Parameters\n   -----------------------------\n   Principal components of anisotropic part of B affecting observed amplitudes:\n     eigenB (A^2)     direction cosines (orthogonal coordinates)\n        25.329              1.0000  -0.0000  -0.0000\n       -12.174              0.0000   0.0000   1.0000\n       -13.155              0.0000   1.0000  -0.0000\n   Anisotropic deltaB (i.e. range of principal components):  38.484\n   Resharpening B (to restore strong direction of diffraction): -13.155\n   Wilson scale applied to get observed intensities: 4.1357e-01\n\n--------------\nABSOLUTE SCALE\n--------------\n\n   Scale factor to put input Fs on absolute scale\n   Wilson Scale:    1.55498\n   Wilson B-factor: 90.4459\n\n------------\nOUTPUT FILES\n------------\n\n   No files output\n\nCPU Time: 0 days 0 hrs 0 mins 25.77 secs (     25.77 secs)\nFinished: Wed Oct 14 14:55:06 2020\n\n*************************************************************************************\n*** Phaser Module: EXPECTED LLG OF ENSEMBLES                                2.6.0 ***\n*************************************************************************************\n\n   Resolution of Data:    3.120\n   Number of Reflections: 17283\n\n   eLLG Values Computed for All Data\n   ---------------------------------\n   target-reso: Resolution to achieve target eLLG of 120\n   Ensemble                   (frac/rms min-max/ expected LLG  ) target-reso\n   \"model\"                    (0.44/0.746-0.746/          637.6)   5.701  \n\nCPU Time: 0 days 0 hrs 0 mins 25.90 secs (     25.90 secs)\nFinished: Wed Oct 14 14:55:06 2020\n\n*************************************************************************************\n*** Phaser Module: TRANSLATIONAL NON-CRYSTALLOGRAPHIC SYMMETRY              2.6.0 ***\n*************************************************************************************\n\n   Unit Cell:   57.87   68.12  235.95   90.00   90.00   90.00\n\n-------------------------------------\nDATA FOR TRANSLATIONAL NCS CORRECTION\n-------------------------------------\n\n   Intensity Moments for Data\n   --------------------------\n   2nd Moment = <E^4>/<E^2>^2 == <J^2>/<J>^2\n                        Untwinned   Perfect Twin\n   2nd Moment  Centric:    3.0          2.0\n   2nd Moment Acentric:    2.0          1.5\n                               Measured\n   2nd Moment  Centric:          4.14\n   2nd Moment Acentric:          2.26\n\n   Resolution for Twin Analysis (85% I/SIGI > 3): 3.50A (HiRes=3.12A)\n\n---------------------\nANISOTROPY CORRECTION\n---------------------\n\n   No refinement of parameters\n\n   Intensity Moments after Anisotropy Correction\n   ---------------------------------------------\n   2nd Moment = <E^4>/<E^2>^2 == <J^2>/<J>^2\n                        Untwinned   Perfect Twin\n   2nd Moment  Centric:    3.0          2.0\n   2nd Moment Acentric:    2.0          1.5\n                               Measured\n   2nd Moment  Centric:          3.85\n   2nd Moment Acentric:          2.03\n\n   Resolution for Twin Analysis (85% I/SIGI > 3): 3.50A (HiRes=3.12A)\n\n------------------------\nTRANSLATIONAL NCS VECTOR\n------------------------\n\n   Space Group :       P 2 2 2\n   Patterson Symmetry: P m m m\n   Resolution of All Data (Number):        3.12 117.97 (17283)\n   Resolution of Patterson (Number):       5.00   9.99 (3783)\n   No translational ncs found or input\n\n   tNCS/Twin Detection Table\n   -------------------------\n   No NCS translation vector\n\n                                 -Second Moments-            --P-values--\n                                 Centric Acentric      untwinned  twin frac <5%\n   Theoretical for untwinned     3.00    2.00    \n   Theoretical for perfect twin  2.00    1.50    \n   Initial (data as input)       4.14    2.26+/-0.068  1          1         \n   After Anisotropy Correction   3.85    2.03+/-0.052  1          1         \n\n   Resolution for Twin Analysis (85% I/SIGI > 3): 3.50A (HiRes=3.12A)\n\n------------\nOUTPUT FILES\n------------\n\n   No files output\n\nCPU Time: 0 days 0 hrs 0 mins 41.45 secs (     41.45 secs)\nFinished: Wed Oct 14 14:55:22 2020\n\n*************************************************************************************\n*** Phaser Module: AUTOMATED MOLECULAR REPLACEMENT                          2.6.0 ***\n*************************************************************************************\n\n*** Z-score test for definite solution is ON\n*** Z-score test for stopping search is OFF\n*** Deep search is OFF\n\nCPU Time: 0 days 0 hrs 0 mins 41.45 secs (     41.45 secs)\nFinished: Wed Oct 14 14:55:22 2020\n\n*************************************************************************************\n*** Phaser Module: EXPERIMENTAL ERROR CORRECTION PREPARATION                2.6.0 ***\n*************************************************************************************\n\n---------------------\nANISOTROPY CORRECTION\n---------------------\n\n   No refinement of parameters\n\n------------------------\nTRANSLATIONAL NCS VECTOR\n------------------------\n\n   Space Group :       P 2 2 2\n   Patterson Symmetry: P m m m\n   Resolution of All Data (Number):        3.12 117.97 (17283)\n   Resolution of Patterson (Number):       5.00   9.99 (3783)\n   No translational ncs found or input\n\n-----------------------------\nEXPERIMENTAL ERROR CORRECTION\n-----------------------------\n\n   Calculate Luzzati D factors accounting for observational error...\n\n   Data have been provided as raw amplitudes\n\n------------\nOUTPUT FILES\n------------\n\n   No files output\n\nCPU Time: 0 days 0 hrs 0 mins 57.37 secs (     57.37 secs)\nFinished: Wed Oct 14 14:55:37 2020\n\n*************************************************************************************\n*** Phaser Module: AUTOMATED MOLECULAR REPLACEMENT                          2.6.0 ***\n*************************************************************************************\n\n*** Search Order (next search *) (placed +):\n*** #1   model *\n*** #2   model  \n\nCPU Time: 0 days 0 hrs 0 mins 57.37 secs (     57.37 secs)\nFinished: Wed Oct 14 14:55:37 2020\n\n*************************************************************************************\n*** Phaser Module: MOLECULAR REPLACEMENT ROTATION FUNCTION                  2.6.0 ***\n*************************************************************************************\n\n---------------------\nANISOTROPY CORRECTION\n---------------------\n\n   No refinement of parameters\n\n------------------------\nTRANSLATIONAL NCS VECTOR\n------------------------\n\n   Space Group :       P 2 2 2\n   Patterson Symmetry: P m m m\n   Resolution of All Data (Number):        3.12 117.97 (17283)\n   Resolution of Patterson (Number):       5.00   9.99 (3783)\n   No translational ncs found or input\n\n--------------------------\nDATA FOR ROTATION FUNCTION\n--------------------------\n\n   High resolution limit input = 4.50\n\n   Outliers with a probability less than 1e-06 will be rejected\n   There were 1 (0.0058%) reflections rejected\n\n      H    K    L   reso     Eo^2    sigma     probability\n      7    9   20   5.05   16.529    0.648       1.010e-07\n\n   Resolution of All Data (Number):        3.12 117.97 (17283)\n   Resolution of Selected Data (Number):   4.50 117.97 (5937)\n\n-------------------\nWILSON DISTRIBUTION\n-------------------\n\n   Parameters set for Wilson log-likelihood calculation\n   E = 0 and variance 1 for each reflection\n   Without correction for SigF to the variances,\n      Wilson log(likelihood) = - number of acentrics (4696)\n                               - half number of centrics (1241/2)\n                             = -5316\n   With correction for SigF,\n      Wilson log(likelihood) = -5256.48\n\n----------\nENSEMBLING\n----------\n\n   Ensemble Generation: model\n   --------------------------\n   Ensemble configured for structure factor interpolation\n   Ensemble configured to resolution 4.50\n   PDB file # 1: 1p7r.cif\n      This pdb file contains 1 model\n      The input RmsD of model #1 with respect to the real structure is 0.75\n\n   Electron Density Calculation\n   0%      100%\n   |=======| DONE\n\n   Weighting Structure Factors\n   0%                                                                      100%\n   |=======================================================================| DONE\n\n   VRMS delta lower/upper limit = -0.506413 / 22.414793\n      RMSD upper limit(s): 4.79\n      RMSD lower limit(s): 0.23\n\n   Ensemble Generation\n   -------------------\n   Resolution of Ensembles: 4.50067\n   Ensemble        Scat% Radius Model# Rel-B Input-RMS Initial-Delta-VRMS Initial-RMS\n   model            44.2  28.34      1  28.5     0.746              0.000       0.746\n\n   Ensemble Generation for Spherical Harmonic Decomposition: model\n   ---------------------------------------------------------------\n   Ensemble configured for spherical harmonic decomposition\n   Ensemble configured to resolution 4.50\n   PDB file # 1: 1p7r.cif\n      This pdb file contains 1 model\n      The input RmsD of model #1 with respect to the real structure is 0.75\n\n   Electron Density Calculation\n   0%      100%\n   |=======| DONE\n\n   Weighting Structure Factors\n   0%                                     100%\n   |======================================| DONE\n\n   VRMS delta lower/upper limit = -0.506413 / 22.414793\n      RMSD upper limit(s): 4.79\n      RMSD lower limit(s): 0.23\n\n   Elmn for Search Ensemble\n   Elmn Calculation for Search Ensemble\n   0%                                                                          100%\n   |===========================================================================| DONE\n\n   Target Function: FAST LERF1\n\n-------------------------\nROTATION FUNCTION #1 OF 1\n-------------------------\n\n   Search Ensemble: model\n\n   Sampling: 4.55 degrees\n\n   SOLU SET \n   SOLU ENSEMBLE model VRMS DELTA +0.0000 RMSD 0.75 #VRMS 0.75\n\n   Spherical Harmonics\n   -------------------\n   Elmn for Data\n   Elmn Calculation for Data\n   0%                                                                         100%\n   |==========================================================================| DONE\n\n   Scanning the Range of Beta Angles\n   ---------------------------------\n   Clmn Calculation\n   0%                                        100%\n   |=========================================| DONE\n\n   Top Peaks Without Clustering\n   Select peaks over 67.5% of top (i.e. 0.675*(top-mean)+mean)\n   There were 585 sites over 67.5% of top\n   585 peaks selected\n   The sites over 67.5% are:\n   #     Euler1 Euler2 Euler3    FSS   Z-score\n   1       56.9   81.0  155.0    100.000  3.79\n   2       53.9   38.7  273.2     98.786  3.75\n   3       69.7   41.8  222.9     97.988  3.72\n   #Sites = 585: output truncated to 3 sites\n\n   Top 585 rotations before clustering will be rescored\n   Calculating Likelihood for RF #1 of 1\n   0%                                                                         100%\n   |==========================================================================| DONE\n\n   Mean and Standard Deviation\n   ---------------------------\n   Scoring 500 randomly sampled rotations\n   Generating Statistics for RF #1 of 1\n   0%                                                                       100%\n   |========================================================================| DONE\n\n   Highest Score (Z-score):  -3.92182   (3.86)\n\n   Top Peaks With Clustering\n   Select peaks over 75% of top (i.e. 0.75*(top-mean)+mean)\n   There were 40 sites over 75% of top\n   The sites over 75% are:\n   #     Euler1 Euler2 Euler3    LLG   Z-score Split #Group  FSS-this-ang/FSS-top\n   1       69.7   41.8  222.9    -3.9218  3.86   0.0      5     97.988/    97.988\n          249.7   41.8  222.9\n          290.3  138.2   42.9\n          110.3  138.2   42.9\n   2       81.2   27.6  156.7    -9.0822  3.57  58.6      5     88.910/    91.822\n          261.2   27.6  156.7\n          278.8  152.4  336.7\n           98.8  152.4  336.7\n   3       58.3   80.8  153.0    -9.9718  3.52  84.3      4     91.519/   100.000\n          238.3   80.8  153.0\n          301.7   99.2  333.0\n          121.7   99.2  333.0\n   #SITES = 40: OUTPUT TRUNCATED TO 3 SITES\n\n   Rotation Function Table: model\n   ------------------------------\n   (Z-scores from Fast Rotation Function)\n   #SET        Top    (Z)      Second    (Z)       Third    (Z)\n   1         -3.92   3.86       -9.08   3.57       -9.97   3.52\n\n---------------\nFINAL SELECTION\n---------------\n\n   Select by Percentage of Top value: 75%\n   Top RF = -3.92182\n   Purge RF mean = -71.661\n   Number of sets stored before final selection = 1\n   Number of solutions stored before final selection = 40\n   Number of sets stored (deleted) after final selection = 1 (0)\n   Number of solutions stored (deleted) after final selection = 3 (37)\n   Number used for purge  = 3\n\n   Rotation Function Final Selection Table\n   ---------------------------------------\n   Rotation list length by SET\n   SET#  Start Final Deleted Set (*)\n      1  40    3           -\n   ALL   40    3    \n\n------------\nOUTPUT FILES\n------------\n\n   No files output\n\nCPU Time: 0 days 0 hrs 1 mins 38.11 secs (     98.11 secs)\nFinished: Wed Oct 14 14:56:18 2020\n\n*************************************************************************************\n*** Phaser Module: MOLECULAR REPLACEMENT TRANSLATION FUNCTION               2.6.0 ***\n*************************************************************************************\n\n---------------------\nANISOTROPY CORRECTION\n---------------------\n\n   No refinement of parameters\n\n------------------------\nTRANSLATIONAL NCS VECTOR\n------------------------\n\n   Space Group :       P 2 2 2\n   Patterson Symmetry: P m m m\n   Resolution of All Data (Number):        3.12 117.97 (17283)\n   Resolution of Patterson (Number):       5.00   9.99 (3783)\n   No translational ncs found or input\n\n-----------------------------\nDATA FOR TRANSLATION FUNCTION\n-----------------------------\n\n   Outliers with a probability less than 1e-06 will be rejected\n   There were 1 (0.0058%) reflections rejected\n\n      H    K    L   reso     Eo^2    sigma     probability\n      7    9   20   5.05   16.529    0.648       1.010e-07\n\n   Resolution of All Data (Number):        3.12 117.97 (17283)\n   Resolution of Selected Data (Number):   4.50 117.97 (5937)\n\n-------------------\nWILSON DISTRIBUTION\n-------------------\n\n   Parameters set for Wilson log-likelihood calculation\n   E = 0 and variance 1 for each reflection\n   Without correction for SigF to the variances,\n      Wilson log(likelihood) = - number of acentrics (4696)\n                               - half number of centrics (1241/2)\n                             = -5316\n   With correction for SigF,\n      Wilson log(likelihood) = -5256.48\n\n------------------------\nALTERNATIVE SPACE GROUPS\n------------------------\n\n   Space Group(s) to be tested:\n     P 21 21 21\n     P 21 21 2\n     P 2 2 21\n     P 21 2 21\n     P 2 21 21\n     P 2 21 2\n     P 21 2 2\n     P 2 2 2\n\n----------\nENSEMBLING\n----------\n\n   Ensemble Generation\n   -------------------\n   Resolution of Ensembles: 4.50067\n   Ensemble        Scat% Radius Model# Rel-B Input-RMS Initial-Delta-VRMS Initial-RMS\n   model            44.2  28.34      1  28.5     0.746              0.000       0.746\n\n---------------------\nTRANSLATION FUNCTIONS\n---------------------\n\n   Target Function: FAST LETF1\n   Sampling: 1.13 Angstroms\n\n----------------------------\nTRANSLATION FUNCTION #1 OF 8\n----------------------------\n\n   Space Group: P 21 21 21\n   SOLU SET \n   SOLU SPAC P 21 21 21\n   SOLU TRIAL ENSEMBLE model EULER 69.729 41.752 222.883 RFZ 3.86\n   SOLU TRIAL ENSEMBLE model EULER 81.204 27.647 156.687 RFZ 3.57\n   SOLU TRIAL ENSEMBLE model EULER 58.325 80.781 152.950 RFZ 3.52\n   SOLU ENSEMBLE model VRMS DELTA +0.0000 RMSD 0.75 #VRMS 0.75\n\n   This TF set has 3 trial orientations\n\n   #TRIAL   Euler1 Euler2 Euler3   Ensemble\n        1     69.7   41.8  222.9   model               \n        2     81.2   27.6  156.7   model               \n        3     58.3   80.8  153.0   model               \n\n   Scoring 501 randomly sampled orientations and translations\n   Generating Statistics for TF SET #1 of 8\n   0%   100%\n   |====| DONE\n\n   Mean Score (Sigma):       -223.23   (21.91)\n\n   SET #1 of 8 TRIAL #1 of 3\n   -------------------------\n   Euler =   69.7   41.8  222.9, Ensemble = model\n\n   Doing Fast Translation Function FFT...\n      Done\n\n   New Top Fast Translation Function FSS = 39.84 (TFZ=4.8) at Trial #1\n\n   Top Peaks Without Clustering\n   Select peaks over 67.5% of top (i.e. 0.675*(top-mean)+mean)\n   There were 89 sites over 67.5% of top\n   89 peaks selected\n   The sites over 67.5% are:\n   #     Frac X Frac Y Frac Z    FSS   Z-score\n   1      0.844  0.823  0.274     39.837  4.82\n   2      0.694  0.201  0.330     30.722  4.39\n   3      0.673  0.149  0.240     30.510  4.38\n   #Sites = 89: output truncated to 3 sites\n\n   Top 89 translations before clustering will be rescored\n   Calculating Likelihood for TF SET #1 of 8 TRIAL #1 of 3\n   0%                                            100%\n   |=============================================| DONE\n\n   New Top (ML) Translation Function LLG = -106.83 (TFZ=5.3) at Trial #1\n   Top Peaks With Clustering\n   Select peaks over 75% of top (i.e. 0.75*(top-mean)+mean)\n   There were 14 sites over 75% of top\n   The sites over 75% are:\n   #     Frac X Frac Y Frac Z    LLG   Z-score Split #Group  FSS-this-xyz/FSS-top\n   1      0.830  0.826  0.322    -106.83  4.17   0.0      1     26.075/    26.075\n   2      0.922  0.908  0.873    -121.23  3.84  53.4      1     19.070/    19.070\n   3      0.873  0.148  0.241    -126.89  4.07  29.3      1     23.768/    23.768\n   #SITES = 14: OUTPUT TRUNCATED TO 3 SITES\n\n   SET #1 of 8 TRIAL #2 of 3\n   -------------------------\n   Euler =   81.2   27.6  156.7, Ensemble = model\n\n   Doing Fast Translation Function FFT...\n      Done\n\n   Current Top Fast Translation Function FSS = 39.84 (TFZ=4.8)\n   Current Top (ML) Translation Function LLG = -106.83 (TFZ=5.3)\n\n   Top Peaks Without Clustering\n   Select peaks over 67.5% of top (i.e. 0.675*(top-mean)+mean)\n   There were 62 sites over 67.5% of top\n   62 peaks selected\n   The sites over 67.5% are:\n   #     Frac X Frac Y Frac Z    FSS   Z-score\n   1      0.323  0.219  0.091     26.406  4.67\n   2      0.007  0.197  0.262     21.767  4.45\n   3      0.427  0.380  0.930     19.581  4.34\n   #Sites = 62: output truncated to 3 sites\n\n   Top 62 translations before clustering will be rescored\n   Calculating Likelihood for TF SET #1 of 8 TRIAL #2 of 3\n   0%                                                              100%\n   |===============================================================| DONE\n\n   Top Peaks With Clustering\n   Select peaks over 75% of top (i.e. 0.75*(top-mean)+mean)\n   There were 42 sites over 75% of top\n   The sites over 75% are:\n   #     Frac X Frac Y Frac Z    LLG   Z-score Split #Group  FSS-this-xyz/FSS-top\n   1      0.323  0.219  0.091    -128.80  4.67   0.0      1     26.406/    26.406\n   2      0.012  0.254  0.941    -129.60  4.26  13.3      1     17.889/    17.889\n   3      0.010  0.193  0.133    -130.66  3.98  20.7      1     12.106/    12.106\n   #SITES = 42: OUTPUT TRUNCATED TO 3 SITES\n\n   SET #1 of 8 TRIAL #3 of 3\n   -------------------------\n   Euler =   58.3   80.8  153.0, Ensemble = model\n\n   Doing Fast Translation Function FFT...\n      Done\n\n   Current Top Fast Translation Function FSS = 39.84 (TFZ=4.8)\n   Current Top (ML) Translation Function LLG = -106.83 (TFZ=5.3)\n\n   Top Peaks Without Clustering\n   Select peaks over 67.5% of top (i.e. 0.675*(top-mean)+mean)\n   There were 17 sites over 67.5% of top\n   17 peaks selected\n   The sites over 67.5% are:\n   #     Frac X Frac Y Frac Z    FSS   Z-score\n   1      0.690  0.742  0.275     20.820  4.51\n   2      0.712  0.666  0.900     17.461  4.35\n   3      0.743  0.839  0.925     14.304  4.20\n   #Sites = 17: output truncated to 3 sites\n\n   Top 17 translations before clustering will be rescored\n   Calculating Likelihood for TF SET #1 of 8 TRIAL #3 of 3\n   0%                 100%\n   |==================| DONE\n\n   Top Peaks With Clustering\n   Select peaks over 75% of top (i.e. 0.75*(top-mean)+mean)\n   There were 13 sites over 75% of top\n   The sites over 75% are:\n   #     Frac X Frac Y Frac Z    LLG   Z-score Split #Group  FSS-this-xyz/FSS-top\n   1      0.743  0.839  0.925    -125.62  4.20   0.0      1     14.304/    14.304\n   2      0.712  0.666  0.900    -127.38  4.35  13.3      1     17.461/    17.461\n   3      0.690  0.742  0.275    -130.59  4.51  53.3      1     20.820/    20.820\n   #SITES = 13: OUTPUT TRUNCATED TO 3 SITES\n\n----------------------------\nTRANSLATION FUNCTION #2 OF 8\n----------------------------\n\n   Space Group: P 21 21 2\n   SOLU SET \n   SOLU SPAC P 21 21 2\n   SOLU TRIAL ENSEMBLE model EULER 69.729 41.752 222.883 RFZ 3.86\n   SOLU TRIAL ENSEMBLE model EULER 81.204 27.647 156.687 RFZ 3.57\n   SOLU TRIAL ENSEMBLE model EULER 58.325 80.781 152.950 RFZ 3.52\n   SOLU ENSEMBLE model VRMS DELTA +0.0000 RMSD 0.75 #VRMS 0.75\n\n   This TF set has 3 trial orientations\n\n   #TRIAL   Euler1 Euler2 Euler3   Ensemble\n        1     69.7   41.8  222.9   model               \n        2     81.2   27.6  156.7   model               \n        3     58.3   80.8  153.0   model               \n\n   Scoring 501 randomly sampled orientations and translations\n   Generating Statistics for TF SET #2 of 8\n   0%   100%\n   |====| DONE\n\n   Mean Score (Sigma):       -223.34   (20.52)\n\n   SET #2 of 8 TRIAL #1 of 3\n   -------------------------\n   Euler =   69.7   41.8  222.9, Ensemble = model\n\n   Doing Fast Translation Function FFT...\n      Done\n\n   New Top Fast Translation Function FSS = 40.52 (TFZ=4.5) at Trial #1\n\n   Top Peaks Without Clustering\n   Select peaks over 67.5% of top (i.e. 0.675*(top-mean)+mean)\n   There were 136 sites over 67.5% of top\n   136 peaks selected\n   The sites over 67.5% are:\n   #     Frac X Frac Y Frac Z    FSS   Z-score\n   1      0.943  0.968  0.080     40.524  4.52\n   2      0.920  0.116  0.949     37.296  4.38\n   3      0.943  0.964  0.056     31.781  4.14\n   #Sites = 136: output truncated to 3 sites\n\n   Top 136 translations before clustering will be rescored\n   Calculating Likelihood for TF SET #2 of 8 TRIAL #1 of 3\n   0%                                                                    100%\n   |=====================================================================| DONE\n\n   Top Peaks With Clustering\n   Select peaks over 75% of top (i.e. 0.75*(top-mean)+mean)\n   There were 81 sites over 75% of top\n   The sites over 75% are:\n   #     Frac X Frac Y Frac Z    LLG   Z-score Split #Group  FSS-this-xyz/FSS-top\n   1      0.713  0.122  0.166    -123.09  4.02   0.0      1     29.052/    29.052\n   2      0.601  0.171  0.023    -123.50  3.91  34.6      1     26.585/    26.585\n   3      0.943  0.964  0.056    -123.68  4.14  31.2      1     31.781/    31.781\n   #SITES = 81: OUTPUT TRUNCATED TO 3 SITES\n\n   SET #2 of 8 TRIAL #2 of 3\n   -------------------------\n   Euler =   81.2   27.6  156.7, Ensemble = model\n\n   Doing Fast Translation Function FFT...\n      Done\n\n   Current Top Fast Translation Function FSS = 40.52 (TFZ=4.5)\n   Current Top (ML) Translation Function LLG = -106.83 (TFZ=5.3)\n\n   Top Peaks Without Clustering\n   Select peaks over 67.5% of top (i.e. 0.675*(top-mean)+mean)\n   There were 56 sites over 67.5% of top\n   56 peaks selected\n   The sites over 67.5% are:\n   #     Frac X Frac Y Frac Z    FSS   Z-score\n   1      0.443  0.326  0.901     22.295  4.22\n   2      0.066  0.198  0.843     21.028  4.16\n   3      0.426  0.188  0.805     20.919  4.16\n   #Sites = 56: output truncated to 3 sites\n\n   Top 56 translations before clustering will be rescored\n   Calculating Likelihood for TF SET #2 of 8 TRIAL #2 of 3\n   0%                                                        100%\n   |=========================================================| DONE\n\n   Top Peaks With Clustering\n   Select peaks over 75% of top (i.e. 0.75*(top-mean)+mean)\n   There were 40 sites over 75% of top\n   The sites over 75% are:\n   #     Frac X Frac Y Frac Z    LLG   Z-score Split #Group  FSS-this-xyz/FSS-top\n   1      0.066  0.198  0.843    -125.86  4.16   0.0      1     21.028/    21.028\n   2      0.443  0.326  0.901    -126.42  4.22  27.2      1     22.295/    22.295\n   3      0.446  0.328  0.177    -128.35  3.68   8.7      1     10.333/    10.333\n   #SITES = 40: OUTPUT TRUNCATED TO 3 SITES\n\n   SET #2 of 8 TRIAL #3 of 3\n   -------------------------\n   Euler =   58.3   80.8  153.0, Ensemble = model\n\n   Doing Fast Translation Function FFT...\n      Done\n\n   Current Top Fast Translation Function FSS = 40.52 (TFZ=4.5)\n   Current Top (ML) Translation Function LLG = -106.83 (TFZ=5.3)\n\n   Top Peaks Without Clustering\n   Select peaks over 67.5% of top (i.e. 0.675*(top-mean)+mean)\n   There were 43 sites over 67.5% of top\n   43 peaks selected\n   The sites over 67.5% are:\n   #     Frac X Frac Y Frac Z    FSS   Z-score\n   1      0.080  0.745  0.929     27.931  4.59\n   2      0.911  0.660  0.924     25.581  4.49\n   3      0.070  0.707  0.368     24.368  4.43\n   #Sites = 43: output truncated to 3 sites\n\n   Top 43 translations before clustering will be rescored\n   Calculating Likelihood for TF SET #2 of 8 TRIAL #3 of 3\n   0%                                           100%\n   |============================================| DONE\n\n   Top Peaks With Clustering\n   Select peaks over 75% of top (i.e. 0.75*(top-mean)+mean)\n   There were 23 sites over 75% of top\n   The sites over 75% are:\n   #     Frac X Frac Y Frac Z    LLG   Z-score Split #Group  FSS-this-xyz/FSS-top\n   1      0.080  0.745  0.929    -123.49  4.59   0.0      1     27.931/    27.931\n   2      0.070  0.794  0.380    -125.12  3.76  78.3      1      9.476/     9.476\n   3      0.911  0.660  0.924    -127.77  4.49  11.4      1     25.581/    25.581\n   #SITES = 23: OUTPUT TRUNCATED TO 3 SITES\n\n----------------------------\nTRANSLATION FUNCTION #3 OF 8\n----------------------------\n\n   Space Group: P 2 2 21\n   SOLU SET \n   SOLU SPAC P 2 2 21\n   SOLU TRIAL ENSEMBLE model EULER 69.729 41.752 222.883 RFZ 3.86\n   SOLU TRIAL ENSEMBLE model EULER 81.204 27.647 156.687 RFZ 3.57\n   SOLU TRIAL ENSEMBLE model EULER 58.325 80.781 152.950 RFZ 3.52\n   SOLU ENSEMBLE model VRMS DELTA +0.0000 RMSD 0.75 #VRMS 0.75\n\n   This TF set has 3 trial orientations\n\n   #TRIAL   Euler1 Euler2 Euler3   Ensemble\n        1     69.7   41.8  222.9   model               \n        2     81.2   27.6  156.7   model               \n        3     58.3   80.8  153.0   model               \n\n   Scoring 501 randomly sampled orientations and translations\n   Generating Statistics for TF SET #3 of 8\n   0%   100%\n   |====| DONE\n\n   Mean Score (Sigma):       -225.22   (21.23)\n\n   SET #3 of 8 TRIAL #1 of 3\n   -------------------------\n   Euler =   69.7   41.8  222.9, Ensemble = model\n\n   Doing Fast Translation Function FFT...\n      Done\n\n   New Top Fast Translation Function FSS = 44.92 (TFZ=5.0) at Trial #1\n\n   Top Peaks Without Clustering\n   Select peaks over 67.5% of top (i.e. 0.675*(top-mean)+mean)\n   There were 43 sites over 67.5% of top\n   43 peaks selected\n   The sites over 67.5% are:\n   #     Frac X Frac Y Frac Z    FSS   Z-score\n   1      0.675  0.793  0.233     44.921  5.01\n   2      0.991  0.823  0.112     23.883  4.03\n   3      0.922  0.150  0.891     23.674  4.02\n   #Sites = 43: output truncated to 3 sites\n\n   Top 43 translations before clustering will be rescored\n   Calculating Likelihood for TF SET #3 of 8 TRIAL #1 of 3\n   0%                                           100%\n   |============================================| DONE\n\n   Top Peaks With Clustering\n   Select peaks over 75% of top (i.e. 0.75*(top-mean)+mean)\n   There were 12 sites over 75% of top\n   The sites over 75% are:\n   #     Frac X Frac Y Frac Z    LLG   Z-score Split #Group  FSS-this-xyz/FSS-top\n   1      0.675  0.793  0.233    -109.17  5.01   0.0      1     44.921/    44.921\n   2      0.922  0.150  0.891    -116.12  4.02  32.8      1     23.674/    23.674\n   3      0.808  0.013  0.179    -132.98  3.75  21.1      1     17.942/    17.942\n   #SITES = 12: OUTPUT TRUNCATED TO 3 SITES\n\n   SET #3 of 8 TRIAL #2 of 3\n   -------------------------\n   Euler =   81.2   27.6  156.7, Ensemble = model\n\n   Doing Fast Translation Function FFT...\n      Done\n\n   Current Top Fast Translation Function FSS = 44.92 (TFZ=5.0)\n   Current Top (ML) Translation Function LLG = -106.83 (TFZ=5.3)\n\n   Top Peaks Without Clustering\n   Select peaks over 67.5% of top (i.e. 0.675*(top-mean)+mean)\n   There were 23 sites over 67.5% of top\n   23 peaks selected\n   The sites over 67.5% are:\n   #     Frac X Frac Y Frac Z    FSS   Z-score\n   1      0.421  0.311  0.256     28.841  4.68\n   2      0.140  0.107  0.905     27.413  4.61\n   3      0.174  0.384  0.207     22.497  4.38\n   #Sites = 23: output truncated to 3 sites\n\n   Top 23 translations before clustering will be rescored\n   Calculating Likelihood for TF SET #3 of 8 TRIAL #2 of 3\n   0%                       100%\n   |========================| DONE\n\n   Top Peaks With Clustering\n   Select peaks over 75% of top (i.e. 0.75*(top-mean)+mean)\n   There were 19 sites over 75% of top\n   The sites over 75% are:\n   #     Frac X Frac Y Frac Z    LLG   Z-score Split #Group  FSS-this-xyz/FSS-top\n   1      0.421  0.311  0.256    -125.84  4.68   0.0      1     28.841/    28.841\n   2      0.140  0.107  0.905    -128.90  4.61  50.2      1     27.413/    27.413\n   3      0.027  0.267  0.924    -133.32  4.27  55.4      1     20.277/    20.277\n   #SITES = 19: OUTPUT TRUNCATED TO 3 SITES\n\n   SET #3 of 8 TRIAL #3 of 3\n   -------------------------\n   Euler =   58.3   80.8  153.0, Ensemble = model\n\n   Doing Fast Translation Function FFT...\n      Done\n\n   Current Top Fast Translation Function FSS = 44.92 (TFZ=5.0)\n   Current Top (ML) Translation Function LLG = -106.83 (TFZ=5.3)\n\n   Top Peaks Without Clustering\n   Select peaks over 67.5% of top (i.e. 0.675*(top-mean)+mean)\n   There were 10 sites over 67.5% of top\n   10 peaks selected\n   The sites over 67.5% are:\n   #     Frac X Frac Y Frac Z    FSS   Z-score\n   1      0.016  0.820  0.317     19.987  4.42\n   2      0.687  0.962  0.071     16.523  4.25\n   3      0.813  0.871  0.159     15.230  4.19\n   #Sites = 10: output truncated to 3 sites\n\n   Top 10 translations before clustering will be rescored\n   Calculating Likelihood for TF SET #3 of 8 TRIAL #3 of 3\n   0%          100%\n   |===========| DONE\n\n   Top Peaks With Clustering\n   Select peaks over 75% of top (i.e. 0.75*(top-mean)+mean)\n   There were 9 sites over 75% of top\n   The sites over 75% are:\n   #     Frac X Frac Y Frac Z    LLG   Z-score Split #Group  FSS-this-xyz/FSS-top\n   1      0.813  0.871  0.159    -128.50  4.19   0.0      1     15.230/    15.230\n   2      0.705  0.857  0.128    -134.49  3.80   9.6      1      6.887/     6.887\n   3      0.687  0.962  0.071    -134.58  4.25  22.7      1     16.523/    16.523\n   #SITES = 9: OUTPUT TRUNCATED TO 3 SITES\n\n----------------------------\nTRANSLATION FUNCTION #4 OF 8\n----------------------------\n\n   Space Group: P 21 2 21\n   SOLU SET \n   SOLU SPAC P 21 2 21\n   SOLU TRIAL ENSEMBLE model EULER 69.729 41.752 222.883 RFZ 3.86\n   SOLU TRIAL ENSEMBLE model EULER 81.204 27.647 156.687 RFZ 3.57\n   SOLU TRIAL ENSEMBLE model EULER 58.325 80.781 152.950 RFZ 3.52\n   SOLU ENSEMBLE model VRMS DELTA +0.0000 RMSD 0.75 #VRMS 0.75\n\n   This TF set has 3 trial orientations\n\n   #TRIAL   Euler1 Euler2 Euler3   Ensemble\n        1     69.7   41.8  222.9   model               \n        2     81.2   27.6  156.7   model               \n        3     58.3   80.8  153.0   model               \n\n   Scoring 501 randomly sampled orientations and translations\n   Generating Statistics for TF SET #4 of 8\n   0%   100%\n   |====| DONE\n\n   Mean Score (Sigma):       -222.68   (22.45)\n\n   SET #4 of 8 TRIAL #1 of 3\n   -------------------------\n   Euler =   69.7   41.8  222.9, Ensemble = model\n\n   Doing Fast Translation Function FFT...\n      Done\n\n   Current Top Fast Translation Function FSS = 44.92 (TFZ=5.0)\n   Current Top (ML) Translation Function LLG = -106.83 (TFZ=5.3)\n\n   Top Peaks Without Clustering\n   Select peaks over 67.5% of top (i.e. 0.675*(top-mean)+mean)\n   There were 74 sites over 67.5% of top\n   74 peaks selected\n   The sites over 67.5% are:\n   #     Frac X Frac Y Frac Z    FSS   Z-score\n   1      0.842  0.820  0.148     38.156  4.66\n   2      0.693  0.871  0.843     34.032  4.47\n   3      0.625  0.182  0.005     30.284  4.29\n   #Sites = 74: output truncated to 3 sites\n\n   Top 74 translations before clustering will be rescored\n   Calculating Likelihood for TF SET #4 of 8 TRIAL #1 of 3\n   0%                                                                          100%\n   |===========================================================================| DONE\n\n   Top Peaks With Clustering\n   Select peaks over 75% of top (i.e. 0.75*(top-mean)+mean)\n   There were 52 sites over 75% of top\n   The sites over 75% are:\n   #     Frac X Frac Y Frac Z    LLG   Z-score Split #Group  FSS-this-xyz/FSS-top\n   1      0.669  0.153  0.174    -118.98  4.03   0.0      1     24.648/    24.648\n   2      0.636  0.804  0.162    -119.15  4.19  24.0      1     27.960/    27.960\n   3      0.693  0.871  0.843    -124.43  4.47  28.7      1     34.032/    34.032\n   #SITES = 52: OUTPUT TRUNCATED TO 3 SITES\n\n   SET #4 of 8 TRIAL #2 of 3\n   -------------------------\n   Euler =   81.2   27.6  156.7, Ensemble = model\n\n   Doing Fast Translation Function FFT...\n      Done\n\n   Current Top Fast Translation Function FSS = 44.92 (TFZ=5.0)\n   Current Top (ML) Translation Function LLG = -106.83 (TFZ=5.3)\n\n   Top Peaks Without Clustering\n   Select peaks over 67.5% of top (i.e. 0.675*(top-mean)+mean)\n   There were 26 sites over 67.5% of top\n   26 peaks selected\n   The sites over 67.5% are:\n   #     Frac X Frac Y Frac Z    FSS   Z-score\n   1      0.173  0.309  0.957     31.294  4.90\n   2      0.017  0.258  0.174     27.812  4.74\n   3      0.016  0.256  0.822     20.876  4.40\n   #Sites = 26: output truncated to 3 sites\n\n   Top 26 translations before clustering will be rescored\n   Calculating Likelihood for TF SET #4 of 8 TRIAL #2 of 3\n   0%                          100%\n   |===========================| DONE\n\n   Top Peaks With Clustering\n   Select peaks over 75% of top (i.e. 0.75*(top-mean)+mean)\n   There were 23 sites over 75% of top\n   The sites over 75% are:\n   #     Frac X Frac Y Frac Z    LLG   Z-score Split #Group  FSS-this-xyz/FSS-top\n   1      0.173  0.309  0.957    -129.36  4.90   0.0      1     31.294/    31.294\n   2      0.016  0.256  0.822    -129.92  4.40  33.3      2     20.876/    27.812\n   3      0.016  0.258  0.111    -135.16  4.34  19.8      1     19.557/    19.557\n   #SITES = 23: OUTPUT TRUNCATED TO 3 SITES\n\n   SET #4 of 8 TRIAL #3 of 3\n   -------------------------\n   Euler =   58.3   80.8  153.0, Ensemble = model\n\n   Doing Fast Translation Function FFT...\n      Done\n\n   Current Top Fast Translation Function FSS = 44.92 (TFZ=5.0)\n   Current Top (ML) Translation Function LLG = -106.83 (TFZ=5.3)\n\n   Top Peaks Without Clustering\n   Select peaks over 67.5% of top (i.e. 0.675*(top-mean)+mean)\n   There were 13 sites over 67.5% of top\n   13 peaks selected\n   The sites over 67.5% are:\n   #     Frac X Frac Y Frac Z    FSS   Z-score\n   1      0.747  0.836  0.923     26.664  4.73\n   2      0.847  0.975  0.922     20.058  4.41\n   3      0.635  0.900  0.933     19.571  4.39\n   #Sites = 13: output truncated to 3 sites\n\n   Top 13 translations before clustering will be rescored\n   Calculating Likelihood for TF SET #4 of 8 TRIAL #3 of 3\n   0%             100%\n   |==============| DONE\n\n   Top Peaks With Clustering\n   Select peaks over 75% of top (i.e. 0.75*(top-mean)+mean)\n   There were 11 sites over 75% of top\n   The sites over 75% are:\n   #     Frac X Frac Y Frac Z    LLG   Z-score Split #Group  FSS-this-xyz/FSS-top\n   1      0.747  0.836  0.923    -126.60  4.73   0.0      1     26.664/    26.664\n   2      0.744  0.838  0.197    -137.25  3.85  40.0      1      8.205/     8.205\n   3      0.687  0.540  0.320    -137.34  3.85  35.5      1      8.124/     8.124\n   #SITES = 11: OUTPUT TRUNCATED TO 3 SITES\n\n----------------------------\nTRANSLATION FUNCTION #5 OF 8\n----------------------------\n\n   Space Group: P 2 21 21\n   SOLU SET \n   SOLU SPAC P 2 21 21\n   SOLU TRIAL ENSEMBLE model EULER 69.729 41.752 222.883 RFZ 3.86\n   SOLU TRIAL ENSEMBLE model EULER 81.204 27.647 156.687 RFZ 3.57\n   SOLU TRIAL ENSEMBLE model EULER 58.325 80.781 152.950 RFZ 3.52\n   SOLU ENSEMBLE model VRMS DELTA +0.0000 RMSD 0.75 #VRMS 0.75\n\n   This TF set has 3 trial orientations\n\n   #TRIAL   Euler1 Euler2 Euler3   Ensemble\n        1     69.7   41.8  222.9   model               \n        2     81.2   27.6  156.7   model               \n        3     58.3   80.8  153.0   model               \n\n   Scoring 501 randomly sampled orientations and translations\n   Generating Statistics for TF SET #5 of 8\n   0%   100%\n   |====| DONE\n\n   Mean Score (Sigma):       -222.94   (20.33)\n\n   SET #5 of 8 TRIAL #1 of 3\n   -------------------------\n   Euler =   69.7   41.8  222.9, Ensemble = model\n\n   Doing Fast Translation Function FFT...\n      Done\n\n   New Top Fast Translation Function FSS = 48.72 (TFZ=5.2) at Trial #1\n\n   Top Peaks Without Clustering\n   Select peaks over 67.5% of top (i.e. 0.675*(top-mean)+mean)\n   There were 28 sites over 67.5% of top\n   28 peaks selected\n   The sites over 67.5% are:\n   #     Frac X Frac Y Frac Z    FSS   Z-score\n   1      0.584  0.074  0.334     48.716  5.23\n   2      0.875  0.930  0.125     30.440  4.37\n   3      0.676  0.043  0.198     28.129  4.26\n   #Sites = 28: output truncated to 3 sites\n\n   Top 28 translations before clustering will be rescored\n   Calculating Likelihood for TF SET #5 of 8 TRIAL #1 of 3\n   0%                            100%\n   |=============================| DONE\n\n   Top Peaks With Clustering\n   Select peaks over 75% of top (i.e. 0.75*(top-mean)+mean)\n   There were 8 sites over 75% of top\n   The sites over 75% are:\n   #     Frac X Frac Y Frac Z    LLG   Z-score Split #Group  FSS-this-xyz/FSS-top\n   1      0.584  0.074  0.334    -107.68  5.23   0.0      1     48.716/    48.716\n   2      0.897  0.230  0.998    -124.61  4.11  49.5      1     24.945/    24.945\n   3      0.676  0.043  0.198    -126.18  4.26  32.7      1     28.129/    28.129\n   #SITES = 8: OUTPUT TRUNCATED TO 3 SITES\n\n   SET #5 of 8 TRIAL #2 of 3\n   -------------------------\n   Euler =   81.2   27.6  156.7, Ensemble = model\n\n   Doing Fast Translation Function FFT...\n      Done\n\n   Current Top Fast Translation Function FSS = 48.72 (TFZ=5.2)\n   Current Top (ML) Translation Function LLG = -106.83 (TFZ=5.3)\n\n   Top Peaks Without Clustering\n   Select peaks over 67.5% of top (i.e. 0.675*(top-mean)+mean)\n   There were 18 sites over 67.5% of top\n   18 peaks selected\n   The sites over 67.5% are:\n   #     Frac X Frac Y Frac Z    FSS   Z-score\n   1      0.320  0.949  0.295     22.269  4.38\n   2      0.026  0.015  0.128     22.087  4.37\n   3      0.432  0.058  0.088     18.988  4.22\n   #Sites = 18: output truncated to 3 sites\n\n   Top 18 translations before clustering will be rescored\n   Calculating Likelihood for TF SET #5 of 8 TRIAL #2 of 3\n   0%                  100%\n   |===================| DONE\n\n   Top Peaks With Clustering\n   Select peaks over 75% of top (i.e. 0.75*(top-mean)+mean)\n   There were 15 sites over 75% of top\n   The sites over 75% are:\n   #     Frac X Frac Y Frac Z    LLG   Z-score Split #Group  FSS-this-xyz/FSS-top\n   1      0.989  0.095  0.831    -133.64  4.12   0.0      1     16.881/    16.881\n   2      0.426  0.057  0.931    -133.85  3.81  34.5      1     10.317/    10.317\n   3      0.267  0.945  0.842    -136.36  3.95  19.2      1     13.329/    13.329\n   #SITES = 15: OUTPUT TRUNCATED TO 3 SITES\n\n   SET #5 of 8 TRIAL #3 of 3\n   -------------------------\n   Euler =   58.3   80.8  153.0, Ensemble = model\n\n   Doing Fast Translation Function FFT...\n      Done\n\n   Current Top Fast Translation Function FSS = 48.72 (TFZ=5.2)\n   Current Top (ML) Translation Function LLG = -106.83 (TFZ=5.3)\n\n   Top Peaks Without Clustering\n   Select peaks over 67.5% of top (i.e. 0.675*(top-mean)+mean)\n   There were 10 sites over 67.5% of top\n   10 peaks selected\n   The sites over 67.5% are:\n   #     Frac X Frac Y Frac Z    FSS   Z-score\n   1      0.985  0.805  0.146     23.108  4.62\n   2      0.022  0.899  0.951     17.124  4.33\n   3      0.986  0.678  0.147     15.620  4.26\n   #Sites = 10: output truncated to 3 sites\n\n   Top 10 translations before clustering will be rescored\n   Calculating Likelihood for TF SET #5 of 8 TRIAL #3 of 3\n   0%          100%\n   |===========| DONE\n\n   Top Peaks With Clustering\n   Select peaks over 75% of top (i.e. 0.75*(top-mean)+mean)\n   There were 10 sites over 75% of top\n   The sites over 75% are:\n   #     Frac X Frac Y Frac Z    LLG   Z-score Split #Group  FSS-this-xyz/FSS-top\n   1      0.986  0.678  0.147    -133.07  4.26   0.0      1     15.620/    15.620\n   2      0.985  0.805  0.146    -135.07  4.62   8.6      1     23.108/    23.108\n   3      0.773  0.807  0.143    -139.04  4.17  15.2      1     13.886/    13.886\n   #SITES = 10: OUTPUT TRUNCATED TO 3 SITES\n\n----------------------------\nTRANSLATION FUNCTION #6 OF 8\n----------------------------\n\n   Space Group: P 2 21 2\n   SOLU SET \n   SOLU SPAC P 2 21 2\n   SOLU TRIAL ENSEMBLE model EULER 69.729 41.752 222.883 RFZ 3.86\n   SOLU TRIAL ENSEMBLE model EULER 81.204 27.647 156.687 RFZ 3.57\n   SOLU TRIAL ENSEMBLE model EULER 58.325 80.781 152.950 RFZ 3.52\n   SOLU ENSEMBLE model VRMS DELTA +0.0000 RMSD 0.75 #VRMS 0.75\n\n   This TF set has 3 trial orientations\n\n   #TRIAL   Euler1 Euler2 Euler3   Ensemble\n        1     69.7   41.8  222.9   model               \n        2     81.2   27.6  156.7   model               \n        3     58.3   80.8  153.0   model               \n\n   Scoring 501 randomly sampled orientations and translations\n   Generating Statistics for TF SET #6 of 8\n   0%   100%\n   |====| DONE\n\n   Mean Score (Sigma):       -224.79   (21.77)\n\n   SET #6 of 8 TRIAL #1 of 3\n   -------------------------\n   Euler =   69.7   41.8  222.9, Ensemble = model\n\n   Doing Fast Translation Function FFT...\n      Done\n\n   Current Top Fast Translation Function FSS = 48.72 (TFZ=5.2)\n   Current Top (ML) Translation Function LLG = -106.83 (TFZ=5.3)\n\n   Top Peaks Without Clustering\n   Select peaks over 67.5% of top (i.e. 0.675*(top-mean)+mean)\n   There were 61 sites over 67.5% of top\n   61 peaks selected\n   The sites over 67.5% are:\n   #     Frac X Frac Y Frac Z    FSS   Z-score\n   1      0.018  0.983  0.861     34.769  4.33\n   2      0.697  0.995  0.079     30.585  4.15\n   3      0.954  0.740  0.991     30.241  4.13\n   #Sites = 61: output truncated to 3 sites\n\n   Top 61 translations before clustering will be rescored\n   Calculating Likelihood for TF SET #6 of 8 TRIAL #1 of 3\n   0%                                                             100%\n   |==============================================================| DONE\n\n   Top Peaks With Clustering\n   Select peaks over 75% of top (i.e. 0.75*(top-mean)+mean)\n   There were 51 sites over 75% of top\n   The sites over 75% are:\n   #     Frac X Frac Y Frac Z    LLG   Z-score Split #Group  FSS-this-xyz/FSS-top\n   1      0.910  0.109  0.248    -123.91  3.76   0.0      2     21.822/    21.822\n   2      0.017  0.979  0.874    -125.22  3.59  38.6      2     18.169/    18.169\n   3      0.670  0.870  0.913    -125.96  3.81  52.0      1     23.113/    23.113\n   #SITES = 51: OUTPUT TRUNCATED TO 3 SITES\n\n   SET #6 of 8 TRIAL #2 of 3\n   -------------------------\n   Euler =   81.2   27.6  156.7, Ensemble = model\n\n   Doing Fast Translation Function FFT...\n      Done\n\n   Current Top Fast Translation Function FSS = 48.72 (TFZ=5.2)\n   Current Top (ML) Translation Function LLG = -106.83 (TFZ=5.3)\n\n   Top Peaks Without Clustering\n   Select peaks over 67.5% of top (i.e. 0.675*(top-mean)+mean)\n   There were 36 sites over 67.5% of top\n   36 peaks selected\n   The sites over 67.5% are:\n   #     Frac X Frac Y Frac Z    FSS   Z-score\n   1      0.003  0.200  0.294     48.341  5.33\n   2      0.064  0.199  0.173     32.541  4.62\n   3      0.171  0.066  0.256     29.522  4.49\n   #Sites = 36: output truncated to 3 sites\n\n   Top 36 translations before clustering will be rescored\n   Calculating Likelihood for TF SET #6 of 8 TRIAL #2 of 3\n   0%                                    100%\n   |=====================================| DONE\n\n   Top Peaks With Clustering\n   Select peaks over 75% of top (i.e. 0.75*(top-mean)+mean)\n   There were 22 sites over 75% of top\n   The sites over 75% are:\n   #     Frac X Frac Y Frac Z    LLG   Z-score Split #Group  FSS-this-xyz/FSS-top\n   1      0.171  0.066  0.256    -118.01  4.49   0.0      1     29.522/    29.522\n   2      0.064  0.199  0.173    -120.38  4.62  22.3      1     32.541/    32.541\n   3      0.234  0.063  0.257    -124.49  3.95   3.7      1     17.656/    17.656\n   #SITES = 22: OUTPUT TRUNCATED TO 3 SITES\n\n   SET #6 of 8 TRIAL #3 of 3\n   -------------------------\n   Euler =   58.3   80.8  153.0, Ensemble = model\n\n   Doing Fast Translation Function FFT...\n      Done\n\n   Current Top Fast Translation Function FSS = 48.72 (TFZ=5.2)\n   Current Top (ML) Translation Function LLG = -106.83 (TFZ=5.3)\n\n   Top Peaks Without Clustering\n   Select peaks over 67.5% of top (i.e. 0.675*(top-mean)+mean)\n   There were 10 sites over 67.5% of top\n   10 peaks selected\n   The sites over 67.5% are:\n   #     Frac X Frac Y Frac Z    FSS   Z-score\n   1      0.893  0.863  0.896     18.275  4.12\n   2      0.631  0.899  0.940     16.682  4.05\n   3      0.985  0.957  0.897     16.584  4.04\n   #Sites = 10: output truncated to 3 sites\n\n   Top 10 translations before clustering will be rescored\n   Calculating Likelihood for TF SET #6 of 8 TRIAL #3 of 3\n   0%          100%\n   |===========| DONE\n\n   Top Peaks With Clustering\n   Select peaks over 75% of top (i.e. 0.75*(top-mean)+mean)\n   There were 10 sites over 75% of top\n   The sites over 75% are:\n   #     Frac X Frac Y Frac Z    LLG   Z-score Split #Group  FSS-this-xyz/FSS-top\n   1      0.893  0.863  0.896    -127.42  4.12   0.0      1     18.275/    18.275\n   2      0.985  0.644  0.898    -128.34  3.71  15.9      1      9.060/     9.060\n   3      0.889  0.867  0.225    -136.72  3.87  32.7      1     12.635/    12.635\n   #SITES = 10: OUTPUT TRUNCATED TO 3 SITES\n\n----------------------------\nTRANSLATION FUNCTION #7 OF 8\n----------------------------\n\n   Space Group: P 21 2 2\n   SOLU SET \n   SOLU SPAC P 21 2 2\n   SOLU TRIAL ENSEMBLE model EULER 69.729 41.752 222.883 RFZ 3.86\n   SOLU TRIAL ENSEMBLE model EULER 81.204 27.647 156.687 RFZ 3.57\n   SOLU TRIAL ENSEMBLE model EULER 58.325 80.781 152.950 RFZ 3.52\n   SOLU ENSEMBLE model VRMS DELTA +0.0000 RMSD 0.75 #VRMS 0.75\n\n   This TF set has 3 trial orientations\n\n   #TRIAL   Euler1 Euler2 Euler3   Ensemble\n        1     69.7   41.8  222.9   model               \n        2     81.2   27.6  156.7   model               \n        3     58.3   80.8  153.0   model               \n\n   Scoring 501 randomly sampled orientations and translations\n   Generating Statistics for TF SET #7 of 8\n   0%   100%\n   |====| DONE\n\n   Mean Score (Sigma):       0.00   (0.00)\n\n   SET #7 of 8 TRIAL #1 of 3\n   -------------------------\n   Euler =   69.7   41.8  222.9, Ensemble = model\n\n   Doing Fast Translation Function FFT...\n      Done\n\n-------------------------------------------------------------------------------------\nFATAL RUNTIME ERROR: WARNING: invalid symmetry flags\n-------------------------------------------------------------------------------------\n\n--------------------\nEXIT STATUS: FAILURE\n--------------------\n\nCPU Time: 0 days 0 hrs 2 mins 35.16 secs (    155.16 secs)\nFinished: Wed Oct 14 14:57:15 2020\n\n</pre>\n</html>\n"}, "spacegroup": "P222", "message": "No solution", "ID": "1P7R", "solution": False}

"""
if not results_json:
    print 'gh'
else:
    print 'gh1'

red = connect_beamline()
print red.get('EIGER_PREFIX_SV')
#print red.get('RUN_PREFIX_SV')
#print red.get('DET_DIST_SV')
#print red.get('DET_THETA_SV')
#print red.get('EIGER_SV')
#print red.get('EIGER_DET_OP_SV')
#print red.keys('*EIGER*')
#print red.keys('*DET*')
#print red.get('ENERGY_SV')
print red.get('EIGER_DIRECTORY_SV')
#print red.keys('*TIME*')

#from mmtbx.command_line import mtz2map
#from utils.xutils import calc_maps
#os.chdir('/gpfs6/users/necat/rapd2/integrate/2020-10-10/2010100103_2/rapd_pdbquery_2010100103_2_1_free/Phaser_4QEQ')
#mtz2map.run(['4QEQ.1.mtz', '4QEQ.1.pdb'])
#utils.xutils.calc_maps(mtz_file='4QEQ.1.mtz', pdb_file='4QEQ.1.pdb')
"""
"""
#result = json.loads(MR_results1)
result = MR_results1
l = ["map_1_1", "map_2_1", 'pdb', 'mtz', 'tar', 'adf', 'peak']
for f in l:
    #if result[f] not in (None, False):
    if result.get(f, False):
        print f
        #archive_dict = result.get(f, {})
        archive_dict = result.get(f, {"path":False})
        print archive_dict
        archive_file = archive_dict.get("path", False)
        if archive_file:
            print 'archive'


f = open('/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_index_CD546A_1_1_2_S.005_CD546A_1_1_2_S.004/result.json', 'r').read()
d = json.loads(f)
print d['results']['mosflm_results_norm']['strategy']['sweeps']



# smartie.py is a python script for parsing log files from CCP4
sys.path.append(os.path.join(os.environ["CCP4"],'share','smartie'))
import smartie

#aimless_log = '/gpfs5/users/necat/rapd/uranium/trunk/integrate/2018-08-01/Alex_2140_1_7000eV_1/Alex_2140_1_7000eV_1/Alex_2140_1_7000eV_1_aimless.log'
aimless_log = '/gpfs5/users/necat/rapd/uranium/trunk/integrate/2018-08-01/Alex_2140_1_7000eV_3/Alex_2140_1_7000eV_3/Alex_2140_1_7000eV_3_aimless.log'
#aimlog = open(aimless_log, 'r').readlines()
#print aimlog
log = smartie.parselog(aimless_log)
# The program expect there to be 10 tables in the aimless log file.
ntables = log.ntables()
if ntables != 10:
    #raise RuntimeError, '%s tables found in aimless output, program expected 10.' %ntables
    print '%s tables found in aimless output, program exepected 10.'

tables = []
for i in range(0,ntables):
    data = []
    # Ignore the Anisotropy analysis table (it's not always present
    # and if you don't ignore it, it causes problems when it is not
    # there.)
    if 'Anisotropy analysis' in log.tables()[i].title():
        pass
    else:
        for line in log.tables()[i].data().split('\n'):
            if line != '':
                data.append(line.split())
        tables.append(data)

print len(tables)
"""
"""
for line in dat_dirs:
    #print line
    if dir.count(line):
        print line

dat_dirs_check = [1 for line in dat_dirs if dir.count(line)]
check = bool(len(dat_dirs_check))
print check
print bool(len([1 for line in dat_dirs if dir.count(line)]))
print bool(len([1 for line in dat_dirs if os.path.dirname(image).count(line)]))

output_dict = {}
search = []
pdb_list = ['0thw', '1thw', '2thw','3thw','4thw','5thw','6thw','7thw']
results = {'0THW' : {'description':'0'},
           '1THW': {'description':'1'},
           '3THW': {'description':'3'},
           '7THW': {'description':'7'}}
for pdb in pdb_list:
    if results.get(pdb.upper(), False):
        output_dict[pdb.upper()] = {'description': results.get(pdb.upper()).get('description')}
    else:
        search.append(pdb)
q = 'pdb_id:(%s)'%" OR ".join(search)
print q
#search = [pdb for pdb in pdb_list if not results.keys().count(pdb)]
#search = [pdb_list.pop(x) for x, pdb in enumerate(pdb_list) if not results.keys().count(pdb.upper())]
#print search
#print pdb_list



image_data = command.get("data", {}).get("image_data")
run_data = command.get("data", {}).get("run_data")

image_data["start"] = run_data.get("start_image_number")
print image_data["start"]
"""


"""
input = ['DATA_RANGE = 1 1200\n']
#tmp = ['DATA_RANGE', '1 1200\n']
#tmp = input[-1].split('=')
#print tmp
#first, last = tmp[-1].split()
first, last = input[-1].split('=')[-1].split()
if int(last) == (int(1)+ int(1200) - 1):
    print 'gh'
#print first, type(first)
#print last, type(last)
"""

"""
cwd = '/gpfs6/users/necat/rapd2/integrate/2018-04-12/L13/rapd_analysis_L13_1_free'
os.chdir(cwd)
#command = "phenix.xtriage %s scaling.input.xray_data.obs_labels=\"I(+),\
#SIGI(+),I(-),SIGI(-)\" scaling.input.parameters.reporting.loggraphs=True" % '/gpfs6/users/necat/rapd2/integrate/2018-04-12/L13/L13_1/L13_1_free.mtz'
command = "molrep -f %s -i << stop\n_DOC  Y\n_RESMAX 4\n_RESMIN 9\nstop"% '/gpfs6/users/necat/rapd2/integrate/2018-04-12/L13/L13_1/L13_1_free.mtz'

pid_queue = Queue()
job = Process(target=process.local_subprocess, kwargs={'command': command,
                                                       'result_queue': pid_queue,
                                                       'logfile' : "molrep_selfrf.log",
                                                       'pid_queue':pid_queue,
                                                       'shell': True})
job.start()
print pid_queue.get()
print pid_queue.get()




cwd = '/gpfs6/users/necat/rapd2/integrate/2018-04-12/L13/rapd_analysis_L13_1_free'
os.chdir(cwd)
# Start logger
#id,_ = os.path.splitext(os.path.basename(fpath))
log = utils.log.get_logger(logfile_dir=cwd, logfile_id='testing')

plugin_queue = Queue()
plugin = plugins.analysis.plugin

analysis_command = {'preferences': {'dir_up': False, 'json': False, 'clean': True, 'nproc': 1, 'test': False, 'progress': False, 'pdbquery': False, 'show_plots': False, 'sample_type': 'default', 'run_mode': 'subprocess'}, 
                    'directories': {'work': u'/gpfs6/users/necat/rapd2/integrate/2018-04-12/L13/rapd_analysis_L13_1_free'}, 
                    'queue': plugin_queue, 
                    'input_data': {'datafile': u'/gpfs6/users/necat/rapd2/integrate/2018-04-12/L13/L13_1/L13_1_free.mtz'}, 
                    'process_id': 'ffbfd87e3e5711e8911c002590757122', 
                    'command': 'ANALYSIS'}


plugin_instance = plugin.RapdPlugin(analysis_command,
                                    logger = log,
                                    verbosity = True
                                    )

plugin_instance.start()

while True:
    analysis_result = plugin_queue.get()
    #self.results["results"]["analysis"] = analysis_result
    #self.send_results(self.results)
    print analysis_result['process']["status"]
    if analysis_result['process']["status"] in (-1, 100):
        print 'end'
        break

#analysis_result = plugin_queue.get()
#pprint(analysis_result)

#with open('/gpfs6/users/necat/Jon/RAPD_test/Output/logfile.log', 'w') as sys.stdout:
job = subprocess.Popen(shlex.split('eiger2cbf /gpfs6/users/necat/Jon/RAPD_test/Images/LSCAT/Ni-edge-n59d-kda28cl36cf57h_001_master.h5 1 /gpfs6/users/necat/Jon/RAPD_test/Output/cbf_files/Ni-edge-n59d-kda28cl36cf57h_001_000001.cbf'),
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
stdout, stderr = job.communicate()
#job.wait()
print stderr


def read_header(image,
                mode=None,
                run_id=None,
                place_in_run=None,
                logger=False):
    
    #Given a full file name for a Piltus image (as a string), read the header and
    #return a dict with all the header info
    
    # print "determine_flux %s" % image
    if logger:
        logger.debug("read_header %s" % image)

    # Make sure the image is a full path image
    image = os.path.abspath(image)
    
    count = 0
    while (count < 10):
        try:
            # Use 'with' to make sure file closes properly. Only read header.
            header = ""
            with open(image, "rb") as raw:
                for line in raw:
                    if line.count('Beam_xy'):
                        line = line.replace('27586.67, 29160.00', '2063.20, 2177.33')
                    header += line
                    #if line.count("Ring_current"):
                    #    break
            break
        except:
            count +=1
            if logger:
                logger.exception('Error opening %s' % image)
            time.sleep(0.1)
    
    new_image = image.replace('ALLER-003_Pn4', 'ALLER-003_Pn4_test')
    with open(new_image, "w") as new:
        new.write(header)
        new.close()
    
    
f = '/gpfs6/users/necat/Jon/RAPD_test/Images/SERCAT/ID/eiger/ALLER-003_Pn4_000100.cbf'
print read_header(f)
"""

"""
proc = subprocess.Popen('qstat',
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

"""
"""
import numpy
header = {}
#site_params = {'BEAM_FLUX': 8.2E11}
site_params = {'BEAM_FLUX': 5E12}
#site_params = {'BEAM_FLUX': 8E11}
header['transmission'] = 100.0
beam_size_x = 0.07
beam_size_y = 0.03
aperture = 0.01
new_x = beam_size_x
new_y = beam_size_y

if aperture < beam_size_x:
    new_x = aperture
if aperture < beam_size_y:
    new_y = aperture

# Calculate area of full beam used to calculate the beamline flux
# Assume ellipse, but same equation works for circle.
# Assume beam is uniform
full_beam_area = numpy.pi*(beam_size_x/2)*(beam_size_y/2)
#print 'full: %s'%full_beam_area

# Calculate the new beam area (with aperture) divided by the full_beam_area.
# Since aperture is round, it will be cutting off edges of x length until it matches beam height,
# then it would switch to circle
if beam_size_y <= aperture:
    # ellipse
    ratio = (numpy.pi*(aperture/2)*(beam_size_y/2)) / full_beam_area
    print 'ration0: %s'%ratio
else:
    # circle
    ratio = (numpy.pi*(aperture/2)**2) / full_beam_area
    print 'ration1: %s'%ratio
# Calculate the new_beam_area ratio to full_beam_area
flux = int(round(site_params.get('BEAM_FLUX') * (header.get('transmission')/100) * ratio))

# Return the flux and beam size
print flux
#return (flux, new_x, new_y)
calc = (8.8E12)/(2*numpy.pi*0.05*0.012)
print calc
calc = (8.8E12)/(numpy.pi*0.035*0.015)
print calc
"""
"""



pool = redis.ConnectionPool(host="164.54.212.169",
            port=6379,
            db=0)

red = redis.StrictRedis(connection_pool=pool)
#red = redis.Redis(connection_pool=pool)
print pool._created_connections, pool._in_use_connections, pool.max_connections
red.set('junk', 'junk')
print pool._created_connections, pool._in_use_connections, pool.max_connections
red.set('junk', '')
pool.disconnect()
print pool._created_connections, pool._in_use_connections, pool.max_connections, pool.pid
#print dir(red.connection_pool)
#print red.connection_pool._created_connections, red.connection_pool.pid
#l = red.client_list()
#for x in range(len(l)):
#    print l[x]['addr'], l[x]['cmd']
#pool.release()
#print pool._created_connections, pool._in_use_connections, pool.max_connections
#print 
"""

"""
f = open('/gpfs2/users/necat/Jon2/process/Minor/K11/P4/Phenix/helix.txt', 'r').readlines()
counter = 0
temp = []
for line in f:
    if line.count('serial_number'):
        counter += 1
        line = line[:line.find('=')+2] + str(counter) + '\n'
    if line.count('helix_identifier'):
        line = '%s"%s"\n'%(line[:line.find('=')+2], str(counter))
        #line = line[:line.find('=')+2] + \"str(counter)\"
    print line
    temp.append(line)
f1 = open('/gpfs2/users/necat/Jon2/process/Minor/K11/P4/Phenix/helix2.txt', 'w')
for line in temp:
    f1.write(line)
f1.close()


import sites.cluster.sercat as cluster
launcher = cluster.process_cluster

import multiprocessing
#import threading
event = multiprocessing.Event()
event.set()
#threading.Thread(target=run_job).start()
processCluster(command='touch junk',
               #work_dir='/gpfs6/users/necat/Jon/RAPD_test/Output',
               work_dir='/gpfs5/users/necat/rapd/rapd2_t/single/2017-08-09/B_14:612',
               logfile='/gpfs6/users/necat/Jon/RAPD_test/Output/temp.log',
               queue='index.q',
               nproc=2,
               name='TEST',
               mp_event=event,
               timeout=False,)
time.sleep(2)
print 'event cleared'
event.clear()

q = Queue()
#q0 = Queue()
#event = Event()
#event.set()
inp_kwargs = {'command': 'sleep 5',
              'logfile': '/home/schuerjp/temp/junk.log',
              'nproc':2,
              'name':'TEST',
              'pid_queue': q,
              #'result_queue': q0,
              #'timeout': 5,
              #'mp_event': event,
              }
# Update batch queue info if using a compute cluster
#inp_kwargs.update(self.batch_queue)

#Launch the job
jobs = Process(target=launcher,
              kwargs=inp_kwargs)
jobs.start()
print q.get()
jobs.join(1)
#print q0.get()
"""
#time.sleep(2)
#print 'event cleared'
#event.clear()

"""
import sites.detectors.necat_dectris_eiger16m as eiger
from detectors.detector_utils import merge_xds_input
#junk = []
l = ['UNTRUSTED_RECTANGLE', 'UNTRUSTED_ELLIPSE', 'UNTRUSTED_QUADRILATERAL']
inp1 = [
      ('TESTING', "TESTING"),
      ('UNTRUSTED_RECTANGLE1', 'TESTING'),
      ('UNTRUSTED_RECTANGLE2', ''),
      ]
for line in merge_xds_input(eiger.XDSINP, inp1):
    print line
"""
#new_inp = []
#for x in range(len(inp1)):
#    for line in eiger.XDSINP:
#        if line.count(inp1[x][0]):
"""
for line in eiger.XDSINP:
    #print "%s%s"%('='.join(line), '\n')
    #if line[0].count('UNTRUSTED_RECTANGLE'):
    #    line = ("UNTRUSTED_RECTANGLE", line[1])
    #print "%s%s"%('='.join(line), '\n')
    #for x in range(len(l)):
    #    if line[0].count(l[x]):
    #        line = (l[x], line[1])
    for x in range(len(inp1)):
        if line[0] == inp1[x][0]:
            line = inp1.pop(x)
    print "%s%s"%('='.join(line), '\n')
if len(inp1) > 0:
    for line in inp1:
        print "%s%s"%('='.join(line), '\n')
"""
"""
labelit_tracker = {}
iteration = 0
#if labelit_tracker.get(iteration, False):
labelit_tracker.setdefault(iteration, {'nruns':0})
print labelit_tracker[iteration].setdefault('nruns', 0)
labelit_tracker[iteration]['nruns'] += 1
print labelit_tracker[iteration]
print labelit_tracker[iteration].get('nruns')
print labelit_tracker[iteration].setdefault('nruns', 0)

labelit_tracker[iteration]['nruns'] += 1

#labelit_tracker.setdefault('nruns', 1)
print labelit_tracker[iteration]
print labelit_tracker[iteration].get('nruns')
print labelit_tracker[iteration].setdefault('nruns', 1)


fin = '/gpfs6/users/necat/Jon/RAPD_test/Output/LWK09_H15_PAIR_0_000001.cbf'
fout = '/gpfs6/users/necat/Jon/RAPD_test/Output/test_01_000001.cbf'

data, header, miniheader = cbf.read(fin, True, True)

print header
print miniheader

cbf.write(fout, data)
"""
"""
file = '/gpfs5/users/necat/capel/images/eiger_test/MDB_CPS66_1_dheader-1.0.raw'
f = open(file,'r').read()
print json.loads(f.bytes)

import time
import os
temp = '/tmp/server.pid'
try:
  with open(temp,'w') as f:
      while True:
        print os.path.isfile(temp)
        time.sleep(2)

except:
  print 'rm -rf %s'%temp
  os.system('rm -rf %s'%temp)
"""
'/ramdisk/gpfs2/users/toronto/tempel_E_2861/images/Raj/runs/test/test2'
"""
#removes test2
#folder = '/ramdisk/gpfs2/users/toronto/tempel_E_2861/images/Raj/runs/test/test2'
folder0 = '/gpfs2/users/GU/UCLA_E_July2017/images/sawaya/sawaya_nnqqnySCN_tray4b1_p13_w12_1/nnqqnySCN_tray4b1_p13_w12_1_000001'
folder1 = '/gpfs2/users/GU/UCLA_E_July2017/images/sawaya/sawaya_nnqqnySCN_tray4b1_p13_w12_1'
#print int(os.popen("ls | wc -l").read())
print int(os.popen("ls /gpfs2/users/GU/UCLA_E_July2017/images/sawaya/sawaya_nnqqnySCN_tray4b1_p13_w12_1/*.cbf| wc -l").read())
print folder0[:folder0.rfind('_')+1]
print int(os.popen("ls %s*.cbf| wc -l"%folder0[:folder0.rfind('_')+1]).read())
"""

#folder = '/ramdisk/gpfs2/users/necat/Jon2/images/eiger_test/junk/junk_1_000001'
#print folder[:folder.rfind('/')]
#shutil.rmtree(folder)
#os.removedirs(folder[:folder.rfind('/')])
#print len([name for name in os.listdir(folder) if os.path.isfile(os.path.join(folder, name))])

"""
for dirpath, subdirs, filenames in os.walk(folder, topdown=False):
  print dirpath
  print subdirs
  print filenames

import tempfile
#fd = tempfile.NamedTemporaryFile(delete=False)
fd = tempfile.NamedTemporaryFile(dir='/gpfs6/users/necat/Jon/RAPD_test/Output', delete=False)
print fd
print fd.name
fd.close()
print fd
print fd.name

from utils.processes import local_subprocess, mp_pool
from multiprocessing import Queue

def f1(command,
       logfile=False,
       pid_queue=False,
       result_queue=False,
       tag=False,
       #*args, **kwargs
       ):
     return command
     print command
     print logfile
     print pid_queue
     print result_queue
     print tag
     pid_queue.put('90')
     result_queue.put('gh')

os.chdir('/gpfs6/users/necat/Jon/RAPD_test/Output')
pool = mp_pool(8)


pid_queue = Queue()
indexing_results_queue = Queue()
# setup input kwargs
command = 'ls'
log = 'junk.log'
iteration = 1

inp_kwargs = {"command": command,
              "logfile": log,
              "pid_queue": pid_queue,
              "result_queue": indexing_results_queue,
              "tag": iteration,
              }
args1 = (command, log, pid_queue, indexing_results_queue, iteration)
launcher = local_subprocess
launcher = f1
#f1(**inp_kwargs)
#f1(*args)
#run = f1(inp_kwargs)
#run = pool.apply_async(f1, kwds=inp_kwargs)
run = pool.apply_async(f1, (inp_kwargs,))
time.sleep(1)
print run.successful()
print dir(run)
print run.__dict__
#print run.get()
print pid_queue.get()
print indexing_results_queue.get()
pool.close()
pool.join()

TIMER = 5
timer = 0
while True:
    if round(timer%TIMER,1) == 1.0:
        print timer
    time.sleep(0.2)
    timer += 0.2
"""


#d = {'fullname': '/gpfs1/users/duke/pei_C_3263/images/pei/runs/A6/0_0/A6_1_0001.cbf !Change to accurate path to data frames'}
#d = {'fullname': '/gpfs1/users/duke/pei_C_3263/images/pei/runs/A6/0_0/A6_1_0001.cbf'}
#print d['fullname'].replace(' !Change to accurate path to data frames', '')

#red = connect_remote_redis()
#red = connect_beamline()
#print red.get('EIGER_NO_FRAME_SV')

#red = connect_sercat_redis()
#connection = connect_beamline()
#red = connect_ft_redis()
#print red.llen('file-tracker-ram')
#print red.llen('file-tracker-nvme')
"""
l = red.keys('/gpfs*')
for k in l:
    print k
    if not red.get(k) in ('ram'):
        print k, red.get(k)

#print os.path.isdir("No key")

#red.delete('RAPD_QSUB_JOBS_0')
#red.delete("images_collected:NECAT_E")
#red.delete("images_collected:NECAT_C")
#red.delete("run_data:NECAT_C")
#red.delete("run_data:NECAT_E")
#red.delete('RAPD_JOBS_WAITING')
#time.sleep(2)
filename = '/gpfs2/users/necat/necat_E_4938/images/jon/snaps/junk_2_000002.cbf'
nr = int(filename[filename.rfind('_')+1:filename.rfind('.')])
#run_number = '_0_'
run_number = ''
#print run_number.split('_')
#print type(run_number.strip('_'))
#print nr
#if os.path.basename(filename).split('_')[-2] not in ('0'):
if str(nr) not in ('1') and os.path.basename(filename).split('_')[-2] not in ('0'):

    print 'gh'
else:
    print 'gh1'

"""

#red.delete('images_collected:NECAT_E')
#red.lpush('images_collected:NECAT_C', '/gpfs1/users/necat/Jon2/images/junk/0_0/tst_0_0001.cbf')
#red.lpush('images_collected:NECAT_E', '/gpfs2/users/harvard/Wagner_E_3064/images/evangelos/snaps/GW02XF07_PAIR_0_000001.cbf')
#red.lpush('images_collected:NECAT_E', '/gpfs2/users/uic/yury_E_3441/images/zahra/snaps/ZB_YSP05_16_GGN_PAIR_0_000005.cbf')
#red.lpush('images_collected:NECAT_E', '/gpfs2/users/necat/necat_E_3100/images/Jon/runs/junk/junk_3_000001.cbf')
#red.lpush('images_collected:NECAT_E', '/gpfs2/users/cwru/kiser_E_3619/images/philip/runs/PDK014_1/PDK014_1_2_000001.cbf')
#red.lpush('images_collected:NECAT_E', '/gpfs2/users/harvard/kahne_E_3623/images/tristan/runs/KAHN012_14/KAHN012_14_1_000001.cbf')
#time.sleep(1)

#runid,first#,total#,dist,energy,transmission,omega_start,deltaomega,time,timestamp
#run_data = ["1","1","465","400","11222.33","15.3","46.0","0.2","0.2",""]
#gpfs_path = '/gpfs1/users/necat/24ID-C_test_oct19/images/bc3/0_0/bc200_PAIR_0_0002.cbf'
#time.sleep(1)
#gpfs_path = '/gpfs5/users/necat/capel/images/eiger2/snaps/test2a_PAIR_0_000010.cbf'
"""
aimlog = '/gpfs5/users/necat/rapd/uranium/trunk/integrate/2020-03-09/CPS_4089_14_1/reprocess_1/aimless.log'
logfile = open(aimlog, 'r').readlines()
for line in logfile:
    if 'High resolution limit' in line:
        current_resolution = line.split()[-1]
    elif 'from half-dataset correlation' in line:
        resline = line
    elif 'from Mn(I/sd) >  1.50' in line:
        resline2 = line
        break
res_cut = resline.split('=')[1].split('A')[0].strip()
print res_cut
res_cut2 = resline2.split('=')[1].split('A')[0].strip()
print res_cut2
if (float(res_cut2) < float(res_cut)):
    res_cut = res_cut2
print res_cut
if (float(res_cut) < (float(current_resolution) + 0.05)):
    res_cut = False
print res_cut
#self.logger.debug('ReIntegration::find_aimless_resolution')
#self.logger.debug('             Cutoff = %s' % res_cut) 
#return(res_cut)
"""

"""
look_for_file = '/epu2/rdma/gpfs1/users/mizzou/tanner_C_5033/images/abogner/runs/TAN008_3/TAN008_3_1_000001/TAN008_3_1_000013.cbf'
#print os.stat(look_for_file)
if os.path.isfile(look_for_file) == True:
    print 'gh'
else:
    print 'gh2'
print glob.glob('%s/*.cbf'%look_for_file[:look_for_file.rfind('/')+1])

command = {u'preferences': {u'json': False, u'cleanup': False, u'run_mode': u'server'}, 
           u'process': {u'image2_id': False, u'status': 0, u'source': u'server', u'session_id': u'6032dafff468330310782adf', u'parent_id': False, 
                        u'image1_id': u'6032dc0df468330310782c6a', u'result_id': u'6032dc0df468330310782c6b'}, 
           u'directories': {u'data_root_dir': u'/gpfs2/users/emory/Dunham_E_5648', u'work': u'/gpfs6/users/necat/rapd2/single/2021-02-21/CMD_4_4_PAIR:2', 
                            u'launch_dir': u'/gpfs6/users/necat/rapd2', u'plugin_directories': [u'sites.plugins', u'plugins']}, 
           u'command': u'INDEX', 
           u'image1': {u'tau': None, u'run_id': None, u'period': 0.2, u'rapd_detector_id': u'necat_dectris_eiger16m', u'sample_mounter_position': u'G4', 
                       u'excluded_pixels': None, u'threshold': 6331.0, u'osc_start': 135.0, u'axis': u'omega', u'image_prefix': u'CMD_4_4_PAIR', u'size1': 4150, 
                       u'size2': 4371, u'osc_range': 0.5, u'site_tag': u'NECAT_E', u'beam_x': 2054.4, u'sensor_thickness': 0.45, u'detector': u'Eiger-16M', 
                       u'count_cutoff': 502255, u'trim_file': None, u'md2_aperture': 0.05, u'n_excluded_pixels': 1198784, u'x_beam_size': 0.05, 
                       u'data_root_dir': u'/gpfs2/users/emory/Dunham_E_5648', u'y_beam_size': 0.02, u'twotheta': 0.0, 
                       u'directory': u'/epu/rdma/gpfs2/users/emory/Dunham_E_5648/images/haan/snaps/CMD_4_4_PAIR_0_000002', u'beam_y': 2194.27, 
                       u'wavelength': 0.97918, u'gain': None, u'date': u'2021-02-20T18:07:13.440534', u'run_number_in_template': True, 
                       u'detector_sn': u'E-32-0108', u'pixel_size': 0.075, u'y_beam': 154.08, u'distance': 350.0, u'run_number': 0, 
                       u'image_template': u'CMD_4_4_PAIR_0_??????.cbf', u'transmission': 28.1, u'collect_mode': u'SNAP', u'flat_field': None, 
                       u'flux': 1405000000000, u'time': 0.1999969, u'x_beam': 164.57025, 
                       u'fullname': u'/gpfs2/users/emory/Dunham_E_5648/images/haan/snaps/CMD_4_4_PAIR_0_000002.cbf', 
                       u'_id': u'6032dc0df468330310782c6a', u'ring_current': 101.8, u'image_number': 2}, 
           u'site_parameters': {u'DETECTOR_DISTANCE_MAX': 1000.0, u'BEAM_CENTER_Y': [154.64591768967472, -0.002128702601888507, 1.6853682723685666e-06, -6.043716204571221e-10], 
                                                                                     u'BEAM_APERTURE_SHAPE': u'circle', u'DETECTOR_DISTANCE_MIN': 150.0, 
                                                                                     u'BEAM_CENTER_DATE': u'2020-02-04', u'DIFFRACTOMETER_OSC_MIN': 0.05, 
                                                                                     u'BEAM_CENTER_X': [165.1427628756774, -0.0014361166886983285, -1.728236304090641e-06, 3.2731939791152326e-09], 
                                                                                     u'BEAM_SIZE_Y': 0.02, u'BEAM_SIZE_X': 0.05, u'DETECTOR_TIME_MIN': 0.05, u'BEAM_FLUX': 5000000000000.0, 
                                                                                     u'BEAM_SHAPE': u'ellipse'},
           u'image2': {u'tau': None, u'run_id': None, u'period': 0.2, u'rapd_detector_id': u'necat_dectris_eiger16m', u'sample_mounter_position': u'G4', 
                       u'excluded_pixels': None, u'threshold': 6331.0, u'osc_start': 135.0, u'axis': u'omega', u'image_prefix': u'CMD_4_4_PAIR', u'size1': 4150, 
                       u'size2': 4371, u'osc_range': 0.5, u'site_tag': u'NECAT_E', u'beam_x': 2054.4, u'sensor_thickness': 0.45, u'detector': u'Eiger-16M', 
                       u'count_cutoff': 502255, u'trim_file': None, u'md2_aperture': 0.05, u'n_excluded_pixels': 1198784, u'x_beam_size': 0.05, 
                       u'data_root_dir': u'/gpfs2/users/emory/Dunham_E_5648', u'y_beam_size': 0.02, u'twotheta': 0.0, 
                       u'directory': u'/epu/rdma/gpfs2/users/emory/Dunham_E_5648/images/haan/snaps/CMD_4_4_PAIR_0_000002', u'beam_y': 2194.27, 
                       u'wavelength': 0.97918, u'gain': None, u'date': u'2021-02-20T18:07:13.440534', u'run_number_in_template': True, 
                       u'detector_sn': u'E-32-0108', u'pixel_size': 0.075, u'y_beam': 154.08, u'distance': 350.0, u'run_number': 0, 
                       u'image_template': u'CMD_4_4_PAIR_0_??????.cbf', u'transmission': 28.1, u'collect_mode': u'SNAP', u'flat_field': None, 
                       u'flux': 1405000000000, u'time': 0.1999969, u'x_beam': 164.57025, 
                       u'fullname': u'/gpfs2/users/emory/Dunham_E_5648/images/haan/snaps/CMD_4_4_PAIR_0_000002.cbf', 
                       u'_id': u'6032dc0df468330310782c6a', u'ring_current': 101.8, u'image_number': 1}, 
           }
preferences = command.get("preferences")
preferences.update({"distl_res_inner" : 30.0,
                    "distl_res_outer" : 3.0,})
image1 = command.get("image1")
image2 = False
test = False
distl_server = ("164.54.212.32", 8125)

from threading import Thread
from utils.processes import local_subprocess
#from multiprocessing import Queue as mp_Queue
import urllib2

def process_distl_server():
        

        
        l = [image1]
        print l[0].get("fullname")
        if image2:
            l.append(image2)
        for i in range(len(l)):
            if test:
                job = Thread(target=local_subprocess,
                             kwargs={"command": 'ls'})
            else:
                url = "http://%s:%d/spotfinder/distl.signal_strength?distl.image=%s&distl.bins.verbose=False&distl.res.outer=%.1f&distl.res.inner=%.1f" \
                    %(distl_server[0], 
                      distl_server[1], 
                      l[i].get("fast_fullname", l[i].get("fullname")), 
                      preferences.get("distl_res_outer", 3.0), 
                      preferences.get("distl_res_inner", 30.0))
                
               
                Response = urllib2.urlopen(url)
                raw = Response.read()
                Response.close()
                result = {'stdout': raw}
                #print result
        
    
process_distl_server()
"""
url = "http://164.54.212.32:8125/spotfinder/distl.signal_strength?distl.image=/gpfs6/users/necat/rapd2/pair/2021-02-21/KH02_2_FL_CHL27_PAIR:1+2/KH02_2_FL_CHL27_PAIR_0_000001.cbf&distl.bins.verbose=False&distl.res.outer=3.0&distl.res.inner=30.0"
url = url.replace("+", "%2b")
print url

"""
#ram_path = '/epu/rdma/gpfs2/users/necat/necat_E_4938/images/Surajit/snaps/NE20_2_1000mm_PAIR_0_000002/NE20_2_1000mm_PAIR_0_000002.cbf'
#ram_path =  '/epu/rdma/gpfs2/users/mskcc/patel_E_4940/images/juncheng/snaps/CPS_0647_8_PAIR_0_000001/CPS_0647_8_PAIR_0_000001.cbf'
ram_path =  '/epu2/rdma/gpfs1/users/upenn/christianson_C_4972/images/corey/snaps/01080_7_PAIR_0_000001/01080_7_PAIR_0_000001.cbf'
#ram_path = '/epu2/rdma/gpfs1/users/necat/24ID-C_feb2020/images/snaps/thaum2_PAIR_0_000001/thaum2_PAIR_0_000001.cbf'
dirname, filename = os.path.split(ram_path)
trim_path = dirname.replace('/ramdisk', '').replace('/epu/rdma', '').replace('/epu2/rdma', '')
gpfs_path = '%s/%s' %(trim_path[:trim_path.rfind('/')], filename)
print gpfs_path
"""
"""
inp = '/ramdisk/gpfs1/users/upenn/christianson_C_4972/images/corey/snaps/01080_7_PAIR_0_000001/01080_7_PAIR_0_000001.cbf'
#nvme_path = inp.replace('/ramdisk', '/epu/rdma')
dirname, filename = os.path.split(inp)
trim_path = dirname.replace('/ramdisk', '').replace('/epu/rdma', '').replace('/epu2/rdma', '')
new_path = os.path.join(trim_path[:trim_path.rfind('/')], filename)
print new_path
"""


#ram_path =  '/epu2/rdma/gpfs5/users/necat/capel/images/eiger2/snaps/test2a_PAIR_0_000010/test2a_PAIR_0_000010.cbf'
#json.dumps([gpfs_path, ram_path])
#red.lpush('images_collected_C', json.dumps([gpfs_path, ram_path]))
#dirname, filename = os.path.split(gpfs_path)
#ram_path = '/epu/rdma%s/%s'%(gpfs_path[:-4],filename)
#print ram_path
#red.lpush('images_collected_E', json.dumps([gpfs_path, ram_path])),

#json.dumps([gpfs_path, inp.replace(Config.RAMDISK_PREFIX, Config.RDMA_PREFIX)])


#red.lpush('images_collected:NECAT_E', '/gpfs2/users/harvard/Wagner_E_3064/images/evangelos/snaps/GW02XF07_PAIR_0_000001.cbf')
#red.lpush('images_collected:NECAT_E', '/gpfs2/users/columbia/hendrickson_E_3093/images/wwang/runs/Hend03_04/Hend03_04_1_001075.cbf')
#red.lpush('images_collected:NECAT_E', '/gpfs2/users/columbia/hendrickson_E_3093/images/wwang/runs/CPS3509_03/CPS3509_03_1_000001.cbf')
#red.lpush('images_collected:NECAT_E', '/gpfs2/users/mskcc/patel_E_3080/images/hui/runs/hy_640_9/hy_640_9_1_000002.cbf')
#red.lpush('images_collected:NECAT_E', '/gpfs2/users/mskcc/patel_E_2891/images/juncheng/snaps/chengwI5_PAIR_0_000005.cbf'),
#red.lpush('images_collected:NECAT_E', '/gpfs2/users/mskcc/patel_E_2891/images/juncheng/snaps/chengwI5_PAIR_0_000006.cbf'),
#red.lpush('images_collected:NECAT_E', '/gpfs2/users/columbia/Mancia_E_3109/images/meagan/snaps/man2_3_0_000001.cbf'), # no index
#red.lpush('images_collected:NECAT_E', '/epu2/rdma/gpfs2/users/slri/sicheri_E_3136/images/Igor/runs/VP03_MKTYc/VP03_MKTYc_1_000001/VP03_MKTYc_1_000001.cbf'),
#red.lpush('images_collected:NECAT_E', '/epu2/rdma/gpfs2/users/slri/sicheri_E_3136/images/Igor/runs/VP03_MKTYc/VP03_MKTYc_1_000001/VP03_MKTYc_1_000002.cbf'),
#red.lpush('images_collected:NECAT_E', '/epu2/rdma/gpfs2/users/harvard/haowu_E_3143/images/liwang/runs/hw1_7/hw1_7_1_000001/hw1_7_1_000001.cbf'),
#red.lpush('images_collected:NECAT_E', '/epu2/rdma/gpfs2/users/upenn/christianson_E_3591/images/nicholas/runs/0004_12/0004_12_1_000001.cbf'),


#red.lpush('images_collected:NECAT_E', '/gpfs2/users/upenn/christianson_E_3591/images/jeremy/runs/JDO_PUCK2_A14_Run4/JDO_PUCK2_A14_Run4_1_000001.cbf'),
#red.lpush('images_collected:NECAT_E', '/gpfs2/users/cornell/heninglin_E_3589/images/ian/runs/P113_11/P113_11_1_000001.cbf'),
#red.lpush('images_collected:NECAT_C', '/gpfs1/users/yale/konigsberg_C_3608/images/aristidis/runs/CPS4580_C1r1/0_0/CPS4580_C1r1_1_0001.cbf'),
#red.lpush('images_collected:NECAT_C', '/gpfs1/users/necat/necat_C_3303/images/Igor/runs/thaum5_05s_05d/0_0/thaum5_05s-05d_1_0001.cbf'),
#red.lpush('images_collected:NECAT_C', '/gpfs1/users/columbia/hendrickson_C_4084/images/liu/runs/BNL138_8/0_0/BNL138_8_1_0937.cbf'),

#red.lpush('images_collected:SERCAT_ID', '/data/ID_GSK_20171101.raw/11_01_2017_APS22id/screen/GSK8P9_AR.0002'),
#red.lpush('images_collected:SERCAT_ID', '/data/ID_MDAnderson_mdanderson.raw/TJ/ATG_70164_07_13/IACS-07_Pn13.0001'),
#red.lpush('images_collected:NECAT_E', '/epu2/rdma/gpfs2/users/sinai/jin_E_3213/images/babault/snaps/JJ1_A3_PAIR_0_000003/JJ1_A3_PAIR_0_000003.cbf')
#red.lpush('images_collected:NECAT_E', '/epu2/rdma/gpfs2/users/yale/strobel_E_3222/images/caroline/runs/SAS001_14/SAS001_14_1_000001/SAS001_14_1_000001.cbf')
#red.lpush('images_collected:SERCAT_ID', '/data/raw/ID_17_11_08_20171108_AMA/CRC-5p2/CRC-5_Pn2.0001'),
#red.lpush('images_collected:SERCAT_ID', '/data/raw/ID_17_11_08_UNC_KE/Puck41_pn7_IDbeam_2/UNC-41_Pn7.0312'),
#red.lpush('images_collected:SERCAT_ID', '/data/ID_GSK_20171101.raw/11_01_2017_APS22id/screen/GSK8P9_AR.0002'),
#red.lpush('images_collected:SERCAT_ID', '/data//raw/BM_17_11_21_GSK_20171121/11_21_2017_APS22bm/screen/P300_GSK3925257A_2_r1_s.0001'),
#red.lpush('images_collected:NECAT_E', '/epu2/rdma/gpfs2/users/fandm/piro_E_3242/images/christine/runs/149pN3F_x04/149pN3F_x04_1_000001/149pN3F_x04_1_000001.cbf')
#red.lpush('images_collected:NECAT_E', '/gpfs2/users/cornell/heninglin_E_3513/images/ian/runs/apr4_127_05nme2/apr4_127_05nme2_1_000001.cbf')
#red.lpush('images_collected:NECAT_C', '/gpfs1/users/upenn/marmorstein_C_3520/images/adam/runs/DF_007_15/0_0/DF_007_15_1_0001.cbf')
#red.lpush('images_collected:NECAT_E', '/gpfs2/users/wustl/yuan_E_3516/images/feifei/runs/py3255/py3255_1_000001.cbf')
#red.lpush('images_collected:NECAT_E', '')
#print red.llen('run_data:NECAT_E')
#r = red.rpop('run_data:NECAT_E')
#red.lpush('runs_data:NECAT_E', r)
#print red.llen('run_data:NECAT_E')
#print red.llen('run_info_E')
#print red.llen('runs_data:NECAT_E')
#print red.llen('runs_data:NECAT_C')
#print red.lrange('runs_data:NECAT_E', 0, -1)
#print red
#red.delete('runs_data:NECAT_E')

#print red.lrange('run_data:NECAT_E', 0, -1)

#print red.llen('current_run_C')
red = connect_rapd2_redis()

#while red.llen('run_info_C'):
#    info = red.rpop('run_info_C')
#    red2.lpush('run_info_C', info)
"""
print red.llen('RAPD_QSUB_JOBS_2')
#red.delete('RAPD_QSUB_JOBS_0')
print red.llen('images_collected:NECAT_E')
#red.delete("images_collected:NECAT_E")
print red.llen('images_collected:NECAT_C')
#red.delete("images_collected:NECAT_C")
print red.llen('run_info_E')
#red.delete('run_info_E')
print red.llen('run_info_C')
#red.delete('run_info_C')
print red.llen('runs_data:NECAT_E')
#print red.lrange('runs_data:NECAT_E', 0, 1)
#red.delete("runs_data:NECAT_E")
print red.llen('runs_data:NECAT_C')
#red.delete("runs_data:NECAT_C")
#print red.lrange('runs_data:NECAT_C', 0, -1)
#red.delete("runs_data:NECAT_C")
print red.llen('RAPD_JOBS_WAITING')
#red.delete('RAPD_JOBS_WAITING')
#print red.llen('RAPD_QSUB_JOBS_2')
#red.delete('RAPD_QSUB_JOBS_2')
print red.llen('RAPD_RESULTS')
"""
