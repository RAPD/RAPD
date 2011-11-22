<?php 
  require('./login/config.php');
  require('./login/functions.php');

  $div_id  = $_GET[div_id];
  //$div_id =  'in_process_38';

  $tmp = preg_split('/_/',$div_id);
  $pro_id = $tmp[2]; 

  //
  // Set the display property of the give result id to hide
  //
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db         = @mysql_select_db('rapd_data',$connection)or die(mysql_error());
  $sql        = "UPDATE processes SET display='hide' WHERE process_id=$pro_id";
  $result     = @mysql_query($sql,$connection) or die(mysql_error());
?>



