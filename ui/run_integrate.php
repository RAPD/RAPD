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
  $sql1          = "SELECT ir.integrate_result_id,ir.pipeline,r.start,r.total FROM integrate_results AS ir JOIN runs AS r ON ir.run_id = r.run_id WHERE result_id=$result_id";
  $result1       = @mysql_query($sql1,$connection) or die(mysql_error());
  $return1       = mysql_fetch_object($result1);
  $integrate_result_id = $return1 -> integrate_result_id;
  $original_type = $return1 -> pipeline;
  $start = $return1 -> start;
  $total = $return1 -> total;
  $finish = $start + $total - 1;
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
  <form id='myForm_integrate' action='./add_integrate.php' method='POST'>
  <!-- HIDDEN VARIABLES POSTED -->
  <input type="hidden" name="original_result_id" value="<? echo($result_id);?>">
  <input type="hidden" name="original_type" id="original_type" value="<? echo($original_type);?>">
  <input type="hidden" name="request_type" value="<? echo($request_type);?>">
  <input type="hidden" name="original_id" value="<? echo($integrate_result_id);?>">
  <input type="hidden" name="datadir" value="<? echo($datadir);?>">
  <input type="hidden" name="ip" value="<? echo($ip_address);?>">
  <table>
    <tr>
      <td align="right" width="225">
        Start image   
      </td>
      <td width="25"></td>
      <td align="left">
        Final Image
      </td>
    </tr>
  </table>
  <table>
    <tr>
      <td align="right" width="218">
        <input type="text" name="start_frame" value="<?echo($start);?>" size=5>
      </td>
      <td width="40"></td>
      <td>
        <input type="text" name="finish_frame" value="<?echo($finish);?>" size=5>
      </td>
    </tr>
  </table>
</form>
</div>
</body>
</html>
