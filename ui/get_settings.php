<?php 
  require('./login/config.php');
  require('./login/functions.php');

  //Start handling the POST
  $datadir = $_GET[datadir];
  $lastid  = $_GET[id];

  //$datadir = '/gpfs2/users/GU/Sazinsky_Aug10';
  //$lastid = 0;

  //make the connection to the database
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db = @mysql_select_db(rapd_data,$connection)or die(mysql_error());        
  
  //Query for newer settings than the UI already has and take only the most recent GLOBAL
  $sql ="SELECT settings.setting_id,reference_data.* FROM settings LEFT JOIN reference_data ON settings.reference_data_id=reference_data.reference_data_id WHERE settings.data_root_dir='$datadir' AND settings.setting_id>$lastid AND settings.setting_type='GLOBAL' ORDER BY settings.setting_id DESC LIMIT 1";
  $result = @mysql_query($sql,$connection) or die(mysql_error());
  
  $arr = array();
  if (mysql_num_rows($result) > 0) {
    $return = mysql_fetch_object($result);
    $setting_id = $return->setting_id;
    $result_array = array();
    $result_array[] = $return->result_id_1;
    $result_array[] = $return->result_id_2;
    $result_array[] = $return->result_id_3;
    $result_array[] = $return->result_id_4;
    $result_array[] = $return->result_id_5;
    $result_array[] = $return->result_id_6;
    $result_array[] = $return->result_id_7;
    $result_array[] = $return->result_id_8;
    $result_array[] = $return->result_id_9;
    $result_array[] = $return->result_id_10;
    $counter = 0;
    foreach ($result_array as $result)
    {
      if (! (is_null($result)))
      {
        $arr[] = $result;
        $counter += 1;
      } else {
        if($counter == 0) 
        {
          $arr[] = 0;
        }
        break;
      }
    }
    $arr[] = $setting_id;

    //Encode in JSON
    $out = json_encode($arr);
    print $out;
  }
?>

