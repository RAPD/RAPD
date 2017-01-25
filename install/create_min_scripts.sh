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
  echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/utils\/overwatch.py --managed_file $SAFE_PREFIX\/src\/gather\/rapd_gather.py \"\$@\"" >>$RAPD_HOME/bin/rapd.gather
  chmod +x $RAPD_HOME/bin/rapd.gather

  # Launcher
  echo "#! /bin/bash" > $RAPD_HOME/bin/rapd.launcher
  echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/utils\/overwatch.py --managed_file $SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/launch\/rapd_launcher.py \"\$@\"" >>$RAPD_HOME/bin/rapd.launcher
  chmod +x $RAPD_HOME/bin/rapd.launcher

  # Launch process
  echo "#! /bin/bash" > $RAPD_HOME/bin/rapd.launch
  echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/launch\/rapd_launch.py \"\$@\"" >>$RAPD_HOME/bin/rapd.launch
  chmod +x $RAPD_HOME/bin/rapd.launch

  # Overwatch
  echo "#! /bin/bash" > $RAPD_HOME/bin/rapd.overwatch
  echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/utils\/overwatch.py \"\$@\"" >>$RAPD_HOME/bin/rapd.overwatch
  chmod +x $RAPD_HOME/bin/rapd.overwatch

  # Generate a new detector scaffold
  echo "#! /bin/bash" > $RAPD_HOME/bin/rapd.generate_detector
  echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/commandline\/generate_detector.py \"\$@\"" >>$RAPD_HOME/bin/rapd.generate_detector
  chmod +x $RAPD_HOME/bin/rapd.generate_detector

# Environmental var not set - don't run
else
  echo "The RAPD_HOME environmental variable must be set. Exiting"
  exit
fi
