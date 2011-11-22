<?php
  //session_start();

  $result_id    = $_POST[result_id];
  $start_repr   = $_POST[start_repr];
  $ip_address   = $_POST[ip];
  $request_type = $_POST[type];  
 
	//$result_id = 106429;
	//$start_repr = "p30_13_2";
  //$ip_address = "164.54.212.43";
	//$request_type = "smerge";

  require('./login/config.php');
  require('./login/functions.php');

  //make the connection to the database
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db = @mysql_select_db('rapd_cloud',$connection)or die(mysql_error());

  //make sure the cloud is open for business
  $sql3 = "SELECT TIMESTAMPDIFF(second,timestamp,CURRENT_TIMESTAMP) FROM cloud_state";
  $result3 = @mysql_query($sql3,$connection) or die(mysql_error()); 
  $return3 = mysql_fetch_row($result3);
  $time = $return3[0];

  $db = @mysql_select_db('rapd_data',$connection)or die(mysql_error());

  //retrive the type, id and setting_id for the given result_id
  $sql1          = "SELECT type,id,setting_id,data_root_dir FROM results WHERE result_id=$result_id";
  $result1       = @mysql_query($sql1,$connection) or die(mysql_error());
  $return1       = mysql_fetch_object($result1);
  $type          = $return1 -> type;
  $id            = $return1 -> id;
  $setting_id    = $return1 -> setting_id;
  $data_root_dir = $return1 -> data_root_dir;

  if ($type == 'integrate') {
    //accumulate images to use in two image processing
    $sql3 ="SELECT id FROM results WHERE data_root_dir='$data_root_dir' AND result_id!=$result_id AND type='integrate' ORDER BY result_id";
    $result3 = @mysql_query($sql3,$connection) or die(mysql_error());

    $new_reprs   = array();
    $new_ids     = array();
    $new_reprs[] = 'None';
    $new_ids     = 'None';
    if (mysql_num_rows($result3) > 0) {
      while ($return3 = mysql_fetch_object($result3)) {
        $integrate_result_id = $return3 -> id;
        $sql4    = "SELECT repr FROM integrate_results WHERE integrate_result_id=$integrate_result_id and integrate_status='SUCCESS'";
        $result4 = @mysql_query($sql4,$connection) or die(mysql_error());
        $return4 =  mysql_fetch_object($result4);
        $repr = $return4 -> repr;
        if (array_search($repr,$new_reprs)) {
        } else {
          $new_reprs[$integrate_result_id] = $repr;
        }
      }
    }
  } else if ($type == 'merge') {
		//accumulate images to use in two image processing
    $sql3 ="SELECT id FROM results WHERE data_root_dir='$data_root_dir' AND type='integrate' ORDER BY result_id";
    $result3 = @mysql_query($sql3,$connection) or die(mysql_error());

    $new_reprs   = array();
    $new_ids     = array();
    $new_reprs[] = 'None';
    $new_ids     = 'None';
    if (mysql_num_rows($result3) > 0) {
      while ($return3 = mysql_fetch_object($result3)) {
        $integrate_result_id = $return3 -> id;
        $sql4    = "SELECT repr FROM integrate_results WHERE integrate_result_id=$integrate_result_id and integrate_status='SUCCESS'";
        $result4 = @mysql_query($sql4,$connection) or die(mysql_error());
        $return4 =  mysql_fetch_object($result4);
        $repr = $return4 -> repr;
        if (array_search($repr,$new_reprs)) {
        } else {
          $new_reprs[$integrate_result_id] = $repr;
        }
      }
    }
	}
?>

<html>
  <head>
  </head>

  <body>
  <div id="content">
  <form id='myForm_merge'>
  <!-- HIDDEN VARIABLES POSTED -->
  <input type="hidden" name="request_type"       value="<? echo($request_type);?>">
  <input type="hidden" name="original_result_id" value="<? echo($result_id);?>">
  <input type="hidden" name="original_type"      value="<? echo($type);?>">
  <input type="hidden" name="original_id"        value="<? echo($id);?>">
  <input type="hidden" name="start_repr"         value="<? echo($start_repr);?>">
  <input type="hidden" name="data_root_dir"      value="<? echo($data_root_dir);?>">
  <input type="hidden" name="ip_address"         value="<? echo($ip_address);?>">

  <table>
    <tr>
      <td align='center' width='550'>
        <h2>Choose dataset to merge with <?echo($start_repr);?></h2>
      </td>
    </tr>
  </table>
  <table>
    <tr>
      <td width='150'>&nbsp;</td>
      <td align='center' width='250'>
<?
     echo("        <select name='merging_dataset'>\n");
     foreach ($new_reprs as $my_id => $repr) {
       echo("          <option value='$my_id::$repr'>$repr</option>\n");
     }
     echo("        </select>\n");
     echo("      </td>\n");
     echo("    </tr>\n");
     echo("  </table>\n");
?>
  </form>
</div>
</body>
</html>
