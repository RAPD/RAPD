<?php

  $result_id    = $_POST[result_id];
  $start_repr   = $_POST[start_repr];
  $ip_address   = $_POST[ip];
  $request_type = $_POST[type];  
  $datadir      = $_POST[datadir];

  //$result_id    = '56457';
  //$start_repr   = 'wedge3_3_1-60';
  //$ip_address   = '164.543.212.22';
  //$request_type = 'start-sad';
  //$datadir      = '/gpfs5/users/necat/EX1_Oct10';

  //require('./login/config.php');
  //require('./login/functions.php');
  require('./custom.php');

  //make the connection to the database
  //$connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  //$db = @mysql_select_db('rapd_cloud',$connection)or die(mysql_error());

  //make sure the cloud is open for business
  //$sql3 = "SELECT TIMESTAMPDIFF(second,timestamp,CURRENT_TIMESTAMP) FROM cloud_state";
  //$result3 = @mysql_query($sql3,$connection) or die(mysql_error()); 
  //$return3 = mysql_fetch_row($result3);
  //$time = $return3[0];

  //$db = @mysql_select_db('rapd_data',$connection)or die(mysql_error());

  //retrive the type, id and setting_id for the given result_id
  //$sql1          = "SELECT integrate_result_id,unmerged_sca_file FROM integrate_results WHERE result_id=$result_id";
  //$result1       = @mysql_query($sql1,$connection) or die(mysql_error());
  //$return1       = mysql_fetch_object($result1);
  //$integrate_result_id = $return1 -> integrate_result_id;
  //$sca_file      = $return1 -> unmerged_sca_file;
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
  <form id='myForm' action='./add_sad.php' method='POST'>
  <!-- HIDDEN VARIABLES POSTED -->
  <input type="hidden" id="form_original_result_id" value="<? echo($result_id);?>">
  <input type="hidden" id="form_request_type" value="<? echo($request_type);?>">
<!--
  <table>
    <tr>
      <td align='center' width='550'>
        <h3>Settings for SAD Structure Solution</h3>
      </td>
    </tr>
  </table>
-->
  <table>
    <tr>
      <td align="right" width="175">
        Anomalous Atom 
      </td>
      <td>
        <select name="ha_type" id="form_ha_type">
<?php
    foreach ($anom_atoms as $a) {
        echo("          <option value='$a'>$a &nbsp; </option>\n");
    }

?>
        </select>
      </td>
    </tr>
    <tr>
      <td align="right" width="175">
        Number of Atoms
      </td>
      <td>
        <select name="ha_number" id="form_ha_number">
          <option value='1'>1 &nbsp; </option>
          <option value='2'>2 &nbsp; </option>
          <option value='3'>3 &nbsp; </option>
          <option value='4'>4 &nbsp; </option>
          <option value='5'>5 &nbsp; </option>
          <option value='6'>6 &nbsp; </option>
          <option value='7'>7 &nbsp; </option>
          <option value='8'>8 &nbsp; </option>
          <option value='9'>9 &nbsp; </option>
          <option value='10'>10 &nbsp; </option>
          <option value='11'>11 &nbsp; </option>
          <option value='12'>12 &nbsp; </option>
          <option value='13'>13 &nbsp; </option>
          <option value='14'>14 &nbsp; </option>
          <option value='15'>15 &nbsp; </option>
          <option value='16'>16 &nbsp; </option>
          <option value='17'>17 &nbsp; </option>
          <option value='18'>18 &nbsp; </option>
          <option value='19'>19 &nbsp; </option>
          <option value='20'>20 &nbsp; </option>
        </select>
      </td>
    </tr>
    <tr>
      <td align="right" width="175">
        Number of ShelxD Trials
      </td>
      <td>
        <input type="text" id="form_shelxd_try" name="form_shelxd_try" value="960" size=5>  
      </td>
    </tr>
    <tr>
      <td align="right" width="175">
        High resolution cutoff
      </td>
      <td>
        <input type="text" id="form_sad_res" name="sad_res" value="0" size=5>  
      </td>
    </tr>
    <tr>
      <td align="right" width="175">
        Sequence (1 letter code)
      </td>
    </tr>
  </table>
  <table>
    <tr>
      <td>
        <TEXTAREA name="sequence" id="form_sequence" rows="5" cols="50"></TEXTAREA>
      </td>
    </tr>
  </table>
</form>
</div>
</body>
</html>
