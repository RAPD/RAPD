<?php 
  require('./login/config.php');
  require('./login/functions.php');

  $res_id  = $_GET[res_id];

  //create output array and store result id as 1st value
  $arr = array();
  $arr[] = $res_id;

  //connect to the db
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db = @mysql_select_db('rapd_data',$connection)or die(mysql_error());
  
  //
  // Grab the sample info using sample_id from results
  //
  $sql = "SELECT samples.* FROM samples,results WHERE samples.sample_id = results.sample_id AND results.result_id = '".$res_id."'";
  $result = @mysql_query($sql,$connection) or die(mysql_error());     
  $sql = mysql_fetch_object($result);
  $sample_id = $sql -> sample_id;
  $crystal = $sql -> CrystalID;
  $project = $sql -> Project;
  $puck = $sql -> PuckID;
  $num = $sql -> sample;
  $protein = $sql -> Protein;

  $arr[] = $sample_id;
  $arr[] = "[".$puck."-".$num."] Sample: ".$crystal." (".$protein.") &nbsp;&nbsp; Project: ".$project;
  //Encode in JSON
  $json = json_encode($arr);
  print $json;
?>