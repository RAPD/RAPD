<?php

//make the connection to the database
require('./login/config.php');
require('./login/functions.php');

$connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());

$db = @mysql_select_db('rapd_data',$connection)or die(mysql_error());

//get variables
$result_ids = json_decode(stripslashes($_POST['result_ids']), true);
$sample_id = $_POST['sample_id'];

foreach ($result_ids as $id) {
   $sql = "SELECT type FROM results WHERE result_id='$id'";
   $result = @mysql_query($sql,$connection) or die(mysql_error());
   $return = mysql_fetch_object($result);
   $result_table = $return -> type;
   $result_table .= "_results";
   //Update results tables with sample_id
   $update = "UPDATE $result_table SET sample_id='$sample_id' WHERE result_id='$id'";
   $uresult = @mysql_query($update,$connection) or die(mysql_error());
   $update = "UPDATE results SET sample_id='$sample_id' WHERE result_id='$id'";
   $uresult = @mysql_query($update,$connection) or die(mysql_error());

   //Update images table with sample_id
   $sql = "SELECT image_id FROM $result_table,results WHERE results.result_id='$id' AND $result_table.result_id=results.result_id";
   $result = @mysql_query($sql,$connection) or die(mysql_error());
   $return = mysql_fetch_object($result);
   $image_id = $return -> image_id;
   $update = "UPDATE images SET sample_id='$sample_id' WHERE image_id='$image_id'";
   $uresult = @mysql_query($update,$connection) or die(mysql_error());


}

 


?>