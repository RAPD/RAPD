#!/bin/bash

# Create scripts used by RAPD

if [ "$RAPD_HOME" != "" ]; then

  SAFE_PREFIX=$(echo "$RAPD_HOME" | sed -e 's/\//\\\//g')

  # Print version
  echo "#! /bin/bash" > $RAPD_HOME/bin/rapd.version
  echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/commandline\/rapd_version.py \"\$@\"" >>$RAPD_HOME/bin/rapd.version
  chmod +x $RAPD_HOME/bin/rapd.version

  # Gather
  echo "#! /bin/bash" > $RAPD_HOME/bin/rapd.gather
  #echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/utils\/overwatch.py --managed_file $SAFE_PREFIX\/src\/gather\/rapd_gather.py \"\$@\"" >>$RAPD_HOME/bin/rapd.gather
  echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/gather\/rapd_gather.py \"\$@\"" >>$RAPD_HOME/bin/rapd.gather
  chmod +x $RAPD_HOME/bin/rapd.gather

  # Launcher
  echo "#! /bin/bash" > $RAPD_HOME/bin/rapd.launcher
  echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/utils\/overwatch.py --managed_file $SAFE_PREFIX\/src\/launch\/rapd_launcher.py \"\$@\"" >>$RAPD_HOME/bin/rapd.launcher
  chmod +x $RAPD_HOME/bin/rapd.launcher

  # Launch process
  echo "#! /bin/bash" > $RAPD_HOME/bin/rapd.launch
  echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/launch\/rapd_launch.py \"\$@\"" >>$RAPD_HOME/bin/rapd.launch
  chmod +x $RAPD_HOME/bin/rapd.launch

  # Overwatch
  echo "#! /bin/bash" > $RAPD_HOME/bin/rapd.overwatch
  echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/utils\/overwatch.py \"\$@\"" >>$RAPD_HOME/bin/rapd.overwatch
  chmod +x $RAPD_HOME/bin/rapd.overwatch

  # Generic generate script
  echo "#! /bin/bash" > $RAPD_HOME/bin/rapd.generate
  echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/generators\/generate.py \"\$@\"" >>$RAPD_HOME/bin/rapd.generate
  chmod +x $RAPD_HOME/bin/rapd.generate

  # Read an XDS input file and make a RAPD XDSINP dict
  echo "#! /bin/bash" > $RAPD_HOME/bin/rapd.xds_to_dict
  echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/utils\/xdsinp_to_dict.py \"\$@\"" >>$RAPD_HOME/bin/rapd.xds_to_dict
  chmod +x $RAPD_HOME/bin/rapd.xds_to_dict

  # Run tests
  echo "#! /bin/bash" > $RAPD_HOME/bin/rapd.test
  echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/test\/test.py \"\$@\"" >>$RAPD_HOME/bin/rapd.test
  chmod +x $RAPD_HOME/bin/rapd.test

# Environmental var not set - don't run
else
  echo "The RAPD_HOME environmental variable must be set. Exiting"
  exit
fi
