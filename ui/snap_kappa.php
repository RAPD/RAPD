<?php

  $result_id    = $_POST[result_id];
  $start_repr   = $_POST[start_repr];
  $ip_address   = $_POST[ip];
  $request_type = $_POST[type];  

  //$result_id = 63662;
  //$start_repr = 'snappair_99_019.img';
  //$ip_address = '164.54.212.15';
  //$request_type = 'stac';

  require('./login/config.php');
  require('./login/functions.php');
  require('./custom.php');

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
  $sql1          = "SELECT type,id,setting_id,data_root_dir FROM results WHERE result_id='$result_id'";
  $result1       = @mysql_query($sql1,$connection) or die(mysql_error());
  $return1       = mysql_fetch_object($result1);
  $type          = $return1 -> type;
  $id            = $return1 -> id;
  $setting_id    = $return1 -> setting_id;
  $data_root_dir = $return1 -> data_root_dir;

  //query for the settings of the retrieved data
  $sql2    = "SELECT * FROM settings WHERE setting_id='$setting_id'";
  $result2 = @mysql_query($sql2,$connection) or die(mysql_error());
  $return2 = mysql_fetch_object($result2);

  //now grab the data to fil the form
  $work_dir_override = $return2 -> work_dir_override;
  $work_directory    = $return2 -> work_directory;

	//get collected datasets for the previous data option
	$sql3 = "SELECT repr,integrate_result_id FROM integrate_results WHERE data_root_dir='$data_root_dir' and integrate_status='SUCCESS'";
	$result3 = @mysql_query($sql3,$connection) or die(mysql_error());
	//$return3 = mysql_fetch_object($result3);
	
?>

<html>
 <body>
  <div id="content">
  <form id='form-snap-kappa'>
    <input type="hidden" name="request_type"       value="<? echo($request_type);?>">
    <input type="hidden" name="original_result_id" value="<? echo($result_id);?>">
    <input type="hidden" name="original_type"      value="<? echo($type);?>">
    <input type="hidden" name="original_id"        value="<? echo($id);?>">
    <input type="hidden" name="setting_id"         value="<? echo($setting_id);?>">
    <input type="hidden" name="data_root_dir"      value="<? echo($data_root_dir);?>">
    <input type="hidden" name="ip_address"         value="<? echo($ip_address);?>">
    <input type="hidden" name="work_dir_override"  value="<? echo($work_dir_override);?>">
    <input type="hidden" name="work_directory"     value="<? echo($work_directory);?>">

  <table>
    <tr>
      <td align="right" width="125">
        MK3 Phi (&deg;) 
      </td>
      <td>
        <input type="text" name="mk3_phi" value="0.0" size=5>
      </td>
    </tr>
    <tr>
      <td align="right" width="125">
        MK3 Kappa (&deg;)
      </td>
      <td>
        <input type="text" name="mk3_kappa" value="0.0" size=5>
      </td>
    </tr>
    <tr>
      <td align="right" width="125">
        Axis alignment 
      </td>
      <td>
        <select name="align_long">
        <option value='smart'>Smart</option>
        <option value='anom'>Anomalous</option>
        <option value='long' selected='selected'>Long</option>
        <option value='a'>a*</option>
        <option value='b'>b*</option>
        <option value='c'>c*</option>
        <option value='ab'>Split a* & b*</option>
        <option value='ac'>Split a* & c*</option>
        <option value='bc'>Split b* & c*</option>
        <option value='all'>a* b* & c*</option>
				<?
				if (mysql_num_rows($result3) > 0) {
				?>
				<option value='multi'>To Previous</option>
				<?
				}
				?>
      	</select>
			</td>
    </tr>
		<?
		if (mysql_num_rows($result3) > 0) {
		?>
		<tr>
		<td align="right" width="125">
      Previous Data 
    </td>
    <td width="175">
      <select name="previous_data">
	    <option value='0'>None</option>
			<?
			while ($return3 = mysql_fetch_object($result3)) {
				$integrate_result_id = $return3 -> integrate_result_id;
				$repr = $return3 -> repr;
				echo("<option value='$integrate_result_id'>$repr</option>\n");
			}
			?>
			</select>
			</td>
			</tr>
			<?
		} else {
			echo('<input type="hidden" name="previous_data"     value="0">');
		}
			?>
  </table
</form>
</div>
</body>
</html>
