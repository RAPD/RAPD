#!/bin/bash

if [ "$RAPD_HOME" != "" ]; then

  SAFE_PREFIX=$(echo "$RAPD_HOME" | sed -e 's/\//\\\//g')

  # Create scripts
  echo "#! /bin/bash" > $RAPD_HOME/bin/rapd.control
  echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/utils\/overwatch.py --managed_file $SAFE_PREFIX\/src\/control\/rapd_control.py \"\$@\"" >>$RAPD_HOME/bin/rapd.control
  chmod +x $RAPD_HOME/bin/rapd.control

  echo "#! /bin/bash" > $RAPD_HOME/bin/rapd.gather
  echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/utils\/overwatch.py --managed_file $SAFE_PREFIX\/src\/gather\/rapd_gather.py \"\$@\"" >>$RAPD_HOME/bin/rapd.gather
  chmod +x $RAPD_HOME/bin/rapd.gather

  echo "#! /bin/bash" > $RAPD_HOME/bin/rapd.launcher
  echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/utils\/overwatch.py --managed_file $SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/launch\/rapd_launcher.py \"\$@\"" >>$RAPD_HOME/bin/rapd.launcher
  chmod +x $RAPD_HOME/bin/rapd.launcher

  echo "#! /bin/bash" > $RAPD_HOME/bin/rapd.launch
  echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/launch\/rapd_launch.py \"\$@\"" >>$RAPD_HOME/bin/rapd.launch
  chmod +x $RAPD_HOME/bin/rapd.launch

  echo "#! /bin/bash" > $RAPD_HOME/bin/rapd.overwatch
  echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/utils\/overwatch.py \"\$@\"" >>$RAPD_HOME/bin/rapd.overwatch
  chmod +x $RAPD_HOME/bin/rapd.overwatch

  echo "#! /bin/bash" > $RAPD_HOME/bin/rapd.index
  echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/commandline\/rapd_index+strategy.py \"\$@\"" >>$RAPD_HOME/bin/rapd.index
  chmod +x $RAPD_HOME/bin/rapd.index

# Environmental var not set - don't run
else
  echo "The RAPD_HOME environmental variable must be set. Exiting"
  exit
fi
