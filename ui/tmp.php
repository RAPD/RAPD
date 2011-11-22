<?php

//prevents caching
header("Expires: Sat, 01 Jan 2000 00:00:00 GMT");
header("Last-Modified: ".gmdate("D, d M Y H:i:s")." GMT");
header("Cache-Control: post-check=0, pre-check=0",false);
session_cache_limiter();
session_start();

require('./login/config.php');

//this should the the absolute path to the functions.php file - see the instrcutions for config.php above
require('./login/functions.php');

if(allow_user() != "yes")
{
    if(allow_local() == "no")
    {
        include ('./login/no_access.html');
        exit();
    }
    else
    {
        $local = allow_local();
    }
}
else
{
    $local = "no";
}
?>
<html>

<head>
  <title>RAPD@NECAT</title>
  <link rel="shortcut icon" href="./css/favicon.ico" type="image/x-icon">
  <style type="text/css" media="screen">
    @import url("css/rapd.css");
  </style>
</head>

<body class='banner'>
  <h1>Welcome to RAPD@NECAT <?php echo $_SESSION[username]; ?></h1>

<div class="clear" style="margin-bottom: 26px;">
  <table align='center'>
    <tr>
      <td>
<? 
    if (allow_access(Administrators) == "yes")
    {
        echo('        <a class="button" href="login/admin/adminpage.php" onclick="this.blur(); return true;"><span>Admin Page</span></a>');
        echo('      </td>');
        echo('      <td>');
        echo('        <a class="button" href="./graphs/index.html" onclick="this.blur(); return true;"><span>Data Stats</span></a>');
        echo('      </td>');
        echo('      <td align="center">');
    }
?>
        <a class="button" href="data_main.php" onclick="this.blur(); return true;"><span>View Data</span></a>
      </td>
      <td>
<?
    if ($local == "no")
    {   
        echo('      <td>');
        echo('        <a class="button" href="samples.php" onclick="this.blur(); return true;"><span>Samples</span></a>');
        echo('      </td>');
        echo('      <td>');
        echo('        <a class="button" href="login/pass_change.html" onclick="this.blur(); return true;"><span>Change Password</span></a>');
        echo('      </td>');
        echo('      <td>');
        echo('        <a class="button" href="login/logout.php" onclick="this.blur(); return true;"><span>Logout</span></a>');
        echo('      </td>');
    }

    if (allow_access(Administrators) == "yes")
    {
        echo('    </tr>');
        echo('    <tr>');
        echo('      <td></td>');
        echo('      <td></td>');
        echo('      <td align="center">');
        echo('        <a class="button" href="data_admin.php" onclick="this.blur(); return true;"><span>Data - Admin View</span></a>');
        echo('      </td>');
        echo('    </tr>');
        echo('    <tr>');
        echo('      <td></td>');
        echo('      <td></td>');
        echo('      <td align="center">');
        echo('        <a class="button" href="data_devel.php" onclick="this.blur(); return true;"><span>Data - Development View</span></a>');
        echo('      </td>');
    }

?>
    </tr>
  </table>
</div>
</body>
</html>

