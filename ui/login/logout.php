<?
include ("config.php");

//destroys the session, the variables are not longer set
session_start();
session_destroy();

?>
<html>
<meta http-equiv="refresh" content="0;url=https://<?php echo $domain; ?>/rapd">
</html>


