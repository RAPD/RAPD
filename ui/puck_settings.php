<?php
  session_start();

  $datadir = $_POST[datadir];
  $beamline  = $_POST[beamline];
  $form_type = "current";
  $username = $_POST[username];
  require('./login/config.php');
  require('./login/functions.php');
?>


<html>
  <body>

<?php
  //make the connection to the database
  $connection = @mysql_connect('rapd', $dbusername, $dbpassword) or die(mysql_error());

  $db = @mysql_select_db('rapd_data',$connection)or die(mysql_error());

  $sql = "SELECT * from current WHERE beamline='$beamline'";
  $result = @mysql_query($sql,$connection) or die(mysql_error());
  $return = mysql_fetch_object($result);

  $current_dir   = $return -> data_root_dir;
  $current_puck  = $return -> puckset_id;
  //obtain current user
  if (allow_user() != "yes")
  {
    echo("You Must Be Logged into Assign Pucks.");
  } else if ($current_dir != $datadir) {
    echo("You Are Not at the Beamline.  You cannot Assign Pucks.");
  } else {

    //query for the pucks for the current user
    $query = "SELECT PuckID FROM samples WHERE username='$username' GROUP BY PuckID";
    $puckresult = @mysql_query($query,$connection) or die(mysql_error());
    $pucks = array();
    while ($row = mysql_fetch_array($puckresult))
      {
        array_push($pucks, $row['0']);
      };    

      //query for the settings of the retrieved data
      $sql1 = "SELECT * FROM puck_settings WHERE puckset_id='$current_puck'";
      $result1 = @mysql_query($sql1,$connection) or die(mysql_error());
      $return1 = mysql_fetch_object($result1);

      //now grab the data to fill the form
      $puck_a   = $return1 -> A;
      $puck_b   = $return1 -> B;
      $puck_c   = $return1 -> C;
      $puck_d   = $return1 -> D;
    
  }


?>


<div id="content">
  <form id='SelectPuck' action='./select_puck.php' method='POST'>
  <!-- HIDDEN VARIABLES POSTED -->
  <input type="hidden" name="datadir"          value="<? echo($datadir);?>">
  <input type="hidden" name="beamline"          value="<? echo($beamline);?>">
<table>
    <tr>
      <td align="right" width="175">
        Puck A
      </td>
      <td width="100">
        <select name="PuckA">
        <option value="None">None</option>
<?php
  foreach ($pucks as $p) {
    if ($p == $puck_a) {
      echo ("          <option value='$p' selected='$p'>$p</option>\n");
    } else {
      echo("          <option value='$p'>$p</option>\n");
    }
  }
?>
        </select> 
      </td>
    </tr>
    <tr>
      <td align="right" width="175">
        Puck B
      </td>
      <td width="100">
        <select name="PuckB">
        <option value="None">None</option>
<?php
  foreach ($pucks as $p) {
    if ($p == $puck_b) {
      echo ("          <option value='$p' selected='$p'>$p</option>\n");
    } else {
      echo("          <option value='$p'>$p</option>\n");
    }
  }
?>
        </select> 
      </td>
    </tr>
    <tr>
      <td align="right" width="175">
        Puck C
      </td>
      <td width="100">
        <select name="PuckC">
        <option value="None">None</option>
<?php
  foreach ($pucks as $p) {
    if ($p == $puck_c) {
      echo ("          <option value='$p' selected='$p'>$p</option>\n");
    } else {
      echo("          <option value='$p'>$p</option>\n");
    }
  }
?>
        </select> 
      </td>
    </tr>
    <tr>
      <td align="right" width="175">
        Puck D
      </td>
      <td width="100">
        <select name="PuckD">
        <option value="None">None</option>
<?php
  foreach ($pucks as $p) {
    if ($p == $puck_d) {
      echo ("          <option value='$p' selected='$p'>$p</option>\n");
    } else {
      echo("          <option value='$p'>$p</option>\n");
    }
  }
?>
        </select> 
      </td>
    </tr>
  </table>

  </form>
</div>

</body>
</html>
