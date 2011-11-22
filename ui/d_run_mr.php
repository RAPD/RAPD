<?php

  $result_id    = $_POST[result_id];
  $start_repr   = $_POST[start_repr];
  $ip_address   = $_POST[ip];
  $request_type = $_POST[type];  
  $user         = $_POST[user];
  $datadir      = $_POST[datadir];
  
  //$result_id    = '56457';
  //$start_repr   = 'wedge3_3_1-60';
  //$ip_address   = '164.543.212.22';
  //$request_type = 'start-sad';
  //$datadir      = '/gpfs5/users/necat/EX1_Oct10';

  require('./login/config.php');
  require('./login/functions.php');
  require('./custom.php');

  //make the connection to the database
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db = @mysql_select_db('rapd_data',$connection)or die(mysql_error());
/*
  //make sure the cloud is open for business
  $sql3 = "SELECT TIMESTAMPDIFF(second,timestamp,CURRENT_TIMESTAMP) FROM cloud_state";
  $result3 = @mysql_query($sql3,$connection) or die(mysql_error()); 
  $return3 = mysql_fetch_row($result3);
  $time = $return3[0];

  $db = @mysql_select_db('rapd_data',$connection)or die(mysql_error());
*/
  //retrive the type, id and setting_id for the given result_id
	$sql0 = "SELECT * FROM results WHERE result_id=$result_id";
	$result0 = @mysql_query($sql0,$connection) or die(mysql_error());
	$return0 = mysql_fetch_object($result0);
	
	$original_type = $return0 -> type;
	
	if ($original_type == "integrate") {
	  $sql1          = "SELECT integrate_result_id,pipeline,mtz_file FROM integrate_results WHERE result_id=$result_id";
	  $result1       = @mysql_query($sql1,$connection) or die(mysql_error());
	  $return1       = mysql_fetch_object($result1);
	  $type_result_id = $return1 -> integrate_result_id;
	  $mtz_file      = $return1 -> mtz_file;
	  //$original_type = $return1 -> pipeline;
	}
	else if ($original_type == "merge"){
		$sql1          = "SELECT merge_result_id,mtz_file FROM merge_results WHERE result_id=$result_id";
	  $result1       = @mysql_query($sql1,$connection) or die(mysql_error());
	  $return1       = mysql_fetch_object($result1);
	  $type_result_id = $return1 -> merge_result_id;
	  $mtz_file      = $return1 -> mtz_file;
	}
  //Now look for previous pdbs that this user may have entered
  $sql2 = "SELECT * from pdbs WHERE username='$user' ORDER BY pdbs_id DESC";
  $result2 = @mysql_query($sql2,$connection) or die(mysql_error());
  $num_rows = mysql_num_rows($result2);

?>

<html>
  <head>
    <style type="text/css">
      h3 {
        color: green;
      }
    </style>
  </head>

  <body>
  <div id="content">

  <form id="myForm_mr" enctype="multipart/form-data" action="uploader.php" method="POST">
    <input type="hidden" name="original_type" id="original_type" value="<? echo($original_type);?>">
    <input type="hidden" name="original_result_id" id="original_result_id" value="<? echo($result_id);?>">
    <input type="hidden" name="request_type" id="request_type" value="<? echo($request_type);?>">
    <input type="hidden" name="original_id" id="original_id" value="<? echo($type_result_id);?>">
    <input type="hidden" name="input_mtz" id="input_mtz" value="<? echo($mtz_file);?>">
    <input type="hidden" name="datadir" id="datadir" value="<? echo($datadir);?>">
    <input type="hidden" name="user" id="user" value="<? echo($user);?>">
    <input type="hidden" name="ip" id="ip" value="<? echo($ip_address);?>">
    <table>
  <!-- PREVIOUS DATA -->
<?
  if ($num_rows > 0)
  {
?>
      <tr>
        <td align="right" width="175">
          Prioir PDB File
        </td>
        <td>
          <select name="prior_pdb" id="prior_pdb">
            <option value="None">&nbsp;</option>
<?
  while ($i = mysql_fetch_object($result2))
  {
    $pdbs_id = $i -> pdbs_id;
    $file = $i -> pdb_file;
    $name = $i -> pdb_name;
    echo("          <option value=\"$pdbs_id\">$file $name </option>\n");
  }
?>          
        </select>
        </td>
      </tr>
			<tr>
				<td></td>
				<td>OR</td>
			</tr>
		</table>
<?
  }
?>
  <!-- UPLOAD -->
  <table>
    <tr>
      <td align="right" width="175">
        Upload PDB File
      </td>
      <td>
        <input id="uploaded_file" name="uploaded_file" type="file"/>                  
      </td>
    </tr>
		<tr>
			<td></td>
			<td>OR</td>
		</tr>
    <tr>
      <td align="right" width="175">
        PDB ID
      </td>
      <td>
        <input type="text" id="pdb_id" name="pdb_id" size=10>
      </td>
		</tr>
		<tr>
			<td align="right" width="175">
				Mol in ASU
			</td>
			<td>
				<select name="nmol" style="width:80px;">
					<option value="0">Auto</option>
					<option value="1">1</option>
					<option value="2">2</option>
					<option value="3">3</option>
					<option value="4">4</option>
					<option value="5">5</option>
					<option value="6">6</option>
					<option value="7">7</option>
					<option value="8">8</option>
					<option value="9">9</option>
				</select>
			</td>
    <tr>
      <td align="right" width="175">
        Job Name (optional)
      </td>
      <td>
        <input type="text" id="formMr_pdb_name" name="pdb_name" size=20>
      </td>
    </tr>
    <tr>
      <td align="right" width="175">
        Job Description (optional)
      </td>
      <td>
        <input type="text" id="pdb_description" name="pdb_description" size=20>
      </td>
    </tr>
  </table>
<iframe id="upload_target" name="upload_target" src="" style="width:0;height:0;border:0px solid #fff;"></iframe>
</form>
</div>
</body>
</html>
