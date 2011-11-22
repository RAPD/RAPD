<?php 
  require('./login/config.php');
  require('./login/functions.php');

  //Start handling the POST
  $id  = $_POST[id];
  $mark = $_POST[mark];

  //make the connection to the database
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db = @mysql_select_db(rapd_cloud,$connection)or die(mysql_error());        

  //build and issue the query
  $sql ="UPDATE cloud_complete SET status='$mark' WHERE cloud_complete_id='$id'";
  $result = @mysql_query($sql,$connection) or die(mysql_error());
?>

