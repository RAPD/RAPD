<?php
   include_once("./login/config.php");
// open a connection to the db
  $connection = @mysql_connect($server,$dbusername,$dbpassword) or die(mysql_error());

// select the db
$db = @mysql_select_db(rapd_data,$connection) or die(mysql_error());

function getPucks($puckset_id, &$array) {
	$sql = "SELECT A,B,C,D from puck_settings WHERE puckset_id='".$puckset_id."'";
     $result = @mysql_query($sql);

     $pucks = mysql_fetch_row($result);

     foreach($pucks as $puck)
       {
          $sql = "SELECT * from samples where PuckID='".$puck."'";
          $result = @mysql_query($sql);
          while($row = mysql_fetch_array($result, MYSQL_NUM))
            {
              array_push($array, $row );
            }
       };
  	 return $array;
  };
  
  function getSamples($user, $data_root_dir, &$array) {
  	$sql = "SELECT samples.* FROM samples,results WHERE samples.username='".$user."' AND samples.sample_id = results.sample_id AND results.data_root_dir = '".$data_root_dir."' GROUP BY samples.sample_id";
     $result = @mysql_query($sql);
     
     while($row = mysql_fetch_array($result, MYSQL_NUM))
       {
           array_push($array, $row );
       };
       return $array;
  };

// set up the query
$user = $_GET['username'];
$data_root_dir = $_GET['datadir'];
$beamline = $_GET['beamline'];

  //create array of sample info
  $arr = array();

// check information in current
  $sql = "SELECT data_root_dir,puckset_id from current WHERE beamline='".$beamline."'";
  $result = @mysql_query($sql);
  $puckset_id = mysql_fetch_row($result);

  // check if user is current
  if ($puckset_id[0] == $data_root_dir) {
    getPucks($puckset_id[1], $arr);
  } else {
    getSamples($user, $data_root_dir, $arr);
  };

  
$aaData = array("aaData" => $arr);
//Encode in JSON
$json = json_encode($aaData);
print $json;


mysql_free_result($result);

?>
