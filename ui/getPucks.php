<?php
   include_once("./login/config.php");
// open a connection to the db
  $connection = @mysql_connect($server,$dbusername,$dbpassword) or die(mysql_error());

// select the db
$db = @mysql_select_db(rapd_data,$connection) or die(mysql_error());

// set up the query
//$user = $_GET['username'];
//$data_root_dir = $_GET['datadir'];
$puckset_id = $_GET['puckset_id'];
$sql = "SELECT A,B,C,D from puck_settings WHERE puckset_id='".$puckset_id."'";
$result = @mysql_query($sql);

$pucks = mysql_fetch_row($result);

//create array of sample info

  $arr = array();

foreach($pucks as $puck)
  {
     $sql = "SELECT * from samples where PuckID='".$puck."'";
     $result = @mysql_query($sql);
     while($row = mysql_fetch_array($result, MYSQL_NUM))
        {
           array_push($arr, $row );
         }
  }

$aaData = array("aaData" => $arr);
//Encode in JSON
$json = json_encode($aaData);
print $json;


mysql_free_result($result);

?>
