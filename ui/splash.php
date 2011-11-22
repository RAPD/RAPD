<?php

//prevents caching
header("Expires: Sat, 01 Jan 2000 00:00:00 GMT");
header("Last-Modified: ".gmdate("D, d M Y H:i:s")." GMT");
header("Cache-Control: post-check=0, pre-check=0",false);
session_cache_limiter();
session_start();

require('./login/config.php');
require('./login/functions.php');

//prevents unauthorized access
if(allow_user() != "yes")
{
    if(allow_local_data($_SESSION[data]) != "yes")
    {
        include ('./login/no_access.html');
        exit();
    }
}

?>
<html>
  <head>
    <style type="text/css" media="screen">
    body {
      background-image: none;
    }
    </style>
  </head>  
  <body class='plain'>
    <h1 class='green'>Here's your data</h1>
    <h3 class='splash'>Select</h3>
    <p class='splash'>The tabs on the left side of the screen will constantly update
                      with new data as it is collected. You may select to see only 
                      snaps, runs or both in one display. Click on a given image or run
                      and the contents of the middle tabs will change.</p>
    <h3 class='splash'>Display</h3>
    <p class='splash'>The middle tabs display what information is available for the selected image or run.</p>
    <p class='splash'><b>Summary</b> gives you the most relevant information pared-down for quick reading.</p>
    <p class='splash'><b>MiniKappa</b> gives you strategies when you are using the minikappa.</p>
    <p class='splash'><b>Detail</b> gives you much more verbose information with option for viewing the full log files.</p>
    <p class='splash'><b>Images</b> allows you to view the image(s) associated with the selected data with predictions.</p>
    <p class='splash'><b>Plots</b> presents data graphically.</p>
    <p class='splash'><b>Ranking</b> - displays all snaps and paired images successfully analyzed in a table which can be sorted by each column - click the column label to do so. The WebIce column is a statistic that convolutes resolution limit, mosaicity and rmsd of spots to predictions - this is the same statistic as calculated by WebIce - higher is better and above 0.6 is considered good. </p>
    <h3 class='splash'>Control</h3>
    <p class='splash'>Main Page will take you back to the screen you see when logging in and
                      Settings will allow you to control settings used during processing. 
                      Saving settings before your start will be saved and used upon your initial
                      data processing.</p>
    <h3 class='splash'>Usage</h3>
    <p class='splash'><b>Snaps</b> - All snaps will be processed. It is strongly urged to take images in pairs (90 degrees apart optimally). They will be processed together if you have the word "pair" in the image name and the names of the images are identical, except for the image number, of course. For example: myprot_pair_1_001.img and myprot_pair_1_002.img will be processed together.</p>
    <p class='splash'><b>Runs</b> - All runs will be processed.</p>
    <p class='splash'>Right-click on snaps and runs to access actions you can take on the data such as hiding, displayin onformation and downloading</p> 
  </body>
</html>
