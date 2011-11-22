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
    <h3 class='splash'>No image display for runs.</h3>
  </body>
</html>
