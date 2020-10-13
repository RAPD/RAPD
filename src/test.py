#import cbf
import json
import shutil
import os
import redis
from redis.sentinel import Sentinel
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
    pool = redis.ConnectionPool(host="164.54.212.56",
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

#log_path = "/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_mr.log"
#dir, log_name = os.path.split(log_path)
#print log_name[:log_name.rfind(".")]

#from mmtbx.command_line import mtz2map
from utils.xutils import calc_maps
os.chdir('/gpfs6/users/necat/rapd2/integrate/2020-10-10/2010100103_2/rapd_pdbquery_2010100103_2_1_free/Phaser_4QEQ')
#mtz2map.run(['4QEQ.1.mtz', '4QEQ.1.pdb'])
utils.xutils.calc_maps(mtz_file='4QEQ.1.mtz', pdb_file='4QEQ.1.pdb')

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
"""

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

#print red.llen('RAPD_QSUB_JOBS_2')
#red.delete('RAPD_QSUB_JOBS_0')
#print red.llen('images_collected:NECAT_E')
#red.delete("images_collected:NECAT_E")
#print red.llen('images_collected:NECAT_C')
#red.delete("images_collected:NECAT_C")
#print red.llen('run_info_E')
#red.delete('run_info_E')
#print red.llen('run_info_C')
#red.delete('run_info_C')
#print red.llen('runs_data:NECAT_E')
#print red.lrange('runs_data:NECAT_E', 0, 1)
#red.delete("runs_data:NECAT_E")
#print red.llen('runs_data:NECAT_C')
#red.delete("runs_data:NECAT_C")
#print red.lrange('runs_data:NECAT_C', 0, -1)
#red.delete("runs_data:NECAT_C")
#print red.llen('RAPD_JOBS_WAITING')
#red.delete('RAPD_JOBS_WAITING')
#print red.llen('RAPD_QSUB_JOBS_2')
#red.delete('RAPD_QSUB_JOBS_2')

