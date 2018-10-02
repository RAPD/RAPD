#!/bin/bash

# Create scripts used by RAPD
# These are in addition to those created by the creat_min_scripts

if [ "$RAPD_HOME" != "" ]; then

  SAFE_PREFIX=$(echo "$RAPD_HOME" | sed -e 's/\//\\\//g')

  # MongoDB Tool
  echo "#! /bin/bash" > $RAPD_HOME/bin/rapd.mongotool
  echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/database\/rapd_mongotool.py \"\$@\"" >>$RAPD_HOME/bin/rapd.mongotool
  chmod +x $RAPD_HOME/bin/rapd.mongotool

  # Control
  echo "#! /bin/bash" > $RAPD_HOME/bin/rapd.control
  echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/utils\/overwatch.py --managed_file $SAFE_PREFIX\/src\/control\/rapd_control.py \"\$@\"" >>$RAPD_HOME/bin/rapd.control
  chmod +x $RAPD_HOME/bin/rapd.control

  # Print out basic detctor information
  echo "#! /bin/bash" > $RAPD_HOME/bin/rapd.print_detector
  echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/detectors\/detector_utils.py \"\$@\"" >>$RAPD_HOME/bin/rapd.print_detector
  chmod +x $RAPD_HOME/bin/rapd.print_detector

  # Convert Eiger HDF5 files to CBFs
  echo "#! /bin/bash" > $RAPD_HOME/bin/rapd.h5_to_cbf
  echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/utils\/convert_hdf5_cbf.py \"\$@\"" >>$RAPD_HOME/bin/rapd.h5_to_cbf
  chmod +x $RAPD_HOME/bin/rapd.h5_to_cbf
  ln -s $RAPD_HOME/bin/rapd.h5_to_cbf $RAPD_HOME/bin/rapd.hdf5_to_cbf
  ln -s $RAPD_HOME/bin/rapd.h5_to_cbf $RAPD_HOME/bin/rapd.eiger_to_cbf

  # Index
  echo "#! /bin/bash" > $RAPD_HOME/bin/rapd.index
  echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/plugins\/index\/commandline.py \"\$@\"" >>$RAPD_HOME/bin/rapd.index
  chmod +x $RAPD_HOME/bin/rapd.index

  # Integrate
  echo "#! /bin/bash" > $RAPD_HOME/bin/rapd.integrate
  echo "# Make sure we can run XDS" >> $RAPD_HOME/bin/rapd.integrate
  echo "unamestr=\`uname\`" >> $RAPD_HOME/bin/rapd.integrate
  echo "if [[ \$unamestr == \"Darwin\" ]]; then" >> $RAPD_HOME/bin/rapd.integrate
  echo "   ulimit -s 65532" >> $RAPD_HOME/bin/rapd.integrate
  echo "fi" >> $RAPD_HOME/bin/rapd.integrate
  echo "# Call integrate" >> $RAPD_HOME/bin/rapd.integrate
  echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/plugins\/integrate\/commandline.py \"\$@\"" >>$RAPD_HOME/bin/rapd.integrate
  chmod +x $RAPD_HOME/bin/rapd.integrate

  # Test collected data against PDB
  echo "#! /bin/bash" > $RAPD_HOME/bin/rapd.pdbquery
  echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/plugins\/pdbquery\/commandline.py \"\$@\"" >>$RAPD_HOME/bin/rapd.pdbquery
  chmod +x $RAPD_HOME/bin/rapd.pdbquery

  # Fetch a PDB from PDBQ
  echo "#! /bin/bash" > $RAPD_HOME/bin/rapd.get_pdb
  echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/plugins\/get_cif\/commandline.py --pdb \"\$@\"" >>$RAPD_HOME/bin/rapd.get_pdb
  chmod +x $RAPD_HOME/bin/rapd.get_pdb

  # Assess integrated data set (for imported data)
  echo "#! /bin/bash" > $RAPD_HOME/bin/rapd.assess
  echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/plugins\/assess_integrated_data\/commandline.py \"\$@\"" >>$RAPD_HOME/bin/rapd.assess
  chmod +x $RAPD_HOME/bin/rapd.assess

  # Fetch a CIF from PDBQ
  echo "#! /bin/bash" > $RAPD_HOME/bin/rapd.get_cif
  echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/plugins\/get_cif\/commandline.py \"\$@\"" >>$RAPD_HOME/bin/rapd.get_cif
  chmod +x $RAPD_HOME/bin/rapd.get_cif

  # X-ray Analysis
  echo "#! /bin/bash" > $RAPD_HOME/bin/rapd.analyze
  echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/plugins\/analysis\/commandline.py \"\$@\"" >>$RAPD_HOME/bin/rapd.analyze
  chmod +x $RAPD_HOME/bin/rapd.analyze

# Index                                                                                                    
  echo "#! /bin/bash" > $RAPD_HOME/bin/rapd.hcmerge
  echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/plugins\/hcmerge\/commandline.py \"\$@\"" >>$RAPD_HOME/bin/rapd.hcmerge
  chmod +x $RAPD_HOME/bin/rapd.hcmerge

# Environmental var not set - don't run
else
  echo "The RAPD_HOME environmental variable must be set. Exiting"
  exit
fi
