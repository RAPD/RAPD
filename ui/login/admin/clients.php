<?php

//prevents caching
header("Expires: Sat, 01 Jan 2000 00:00:00 GMT");
header("Last-Modified: ".gmdate("D, d M Y H:i:s")." GMT");
header("Cache-Control: post-check=0, pre-check=0",false);
session_cache_limiter();
session_start();

require('../config.php');
require('../functions.php');

//check for administrative rights
if (allow_access(Administrators) != "yes")
{
	include ('../no_access.html');
	exit;
}

?>

<head>
  <meta http-equiv="Content-Language" content="en-us">

  <style type="text/css" media="screen">
    @import url("../../css/rapd.css");
  </style>
</head>

<body class='banner' topmargin="0" leftmargin="0" rightmargin="0" bottommargin="0">
  <h1>RAPD Clients Administration</h1>
  <table border="0" width="100%" id="table1">
    <tr>
      <td align="center">
        <table border="0" width="800" id="table2" cellspacing="0" cellpadding="0">
	  <tr>
	    <td width="280">&nbsp;</td>
	  </tr>
	  <tr>
	    <td width="280"><b><font size="2">Rapd Clients Control Panel</font></b></td>
	  </tr>
	  <tr>
	    <td width="280">Logged in as <?php echo $_SESSION[username]; ?></td>
	  </tr>
          <tr>
            <td><a href="../../main.php">Main Page</a></td>
          </tr>
          <tr>
            <td><a href="adminpage.php">Administrative Control Panel</a></td>
          </tr>
	  <tr>
	    <td width="280"><a href="../logout.php">Logout</a></td>
	  </tr>
          <tr>
            <td>
              <table border="0" width="100%" id="table4" cellspacing="0" cellpadding="2">
                <tr>
                  <td><caption>Clients Administration</caption>      
<?php

    //require the config file
    require ("../config.php");

    //make the connection to the database
    $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
    $db = @mysql_select_db($db_name,$connection)or die(mysql_error());

    //build and issue the query
    $sql = "SELECT * FROM authorized_clients ORDER BY client_ip";
    $result = @mysql_query($sql,$connection) or die(mysql_error());
    $i = mysql_num_rows($result);
        echo "<tr><table>";
        echo "    <tr><td class='header'>IP Address</td><td class='header'></td>Name<td class='header'>Beamline</td><td class='header'>Entry Timestamp</td></tr>";
    if ($i > 0)
      {
        //echo "<tr><table>";
        //echo "    <tr><td class='header'>IP Address</td><td class='header'></td>Name<td class='header'>Beamline</td><td class='header'>Entry Timestamp</td></tr>";
	$j = 1;
        while ($sql = mysql_fetch_object($result))
	{
	    $client_ip   = $sql -> client_ip;
	    $client_name = $sql -> client_name;
	    $beamline    = $sql -> beamline;
	    $timestamp   = $sql -> timestamp;
	    
	    echo "<FORM METHOD=\"POST\" ACTION=\"removeclient.php\">";
	    if (fmod($j,2) == 0)
            {
                echo "  <tr bgcolor=\"EEEEFF\">";
            }
            else
            {
                echo "  <tr>";
	    }
      echo "    <td><input type=\"hidden\" name=\"client_ip\" value=\"$client_ip\">$client_ip</td>";
	    echo "    <td><input type=\"hidden\" name=\"client_name\" value=\"$client_name\">$client_name</td>";
	    echo "    <td><input type=\"hidden\" name=\"beamline\" value=\"$beamline\">$beamline</td>";
	    echo "    <td><input type=\"hidden\" name=\"timestamp\" value=\"$timestamp\">$timestamp</td>";
	    echo "    <td><input type=\"submit\" value=\"Delete Client\" name=\"submit\"></td>";
	    echo "  </tr>";
            echo "</FORM>";
            $j++;
	}
        //Now the option to add a client
        echo "<FORM METHOD=\"POST\" ACTION=\"addclient.php\">";
        if (fmod($j,2) == 0)
              {
                echo "  <tr bgcolor=\"EEEEFF\">";
              }
            else
              {
                echo "  <tr>";
              }
        echo "    <td><input type=\"text\" name=\"client_ip\" size=\"24\"></td>";
        echo "    <td>&nbsp;</td>";
        echo "    <td><input type=\"text\" name=\"beamline\" size=\"3\"></td>";
        echo "    <td>&nbsp;</td>";
        echo "    <td><input type=\"submit\" value=\"Add Client\" name=\"submit\"></td>";
        echo "  </tr>";
        echo "</FORM>";
        $j++;
      } else {
        echo "<FORM METHOD=\"POST\" ACTION=\"addclient.php\">";
        if (fmod($j,2) == 0)
              {
                echo "  <tr bgcolor=\"EEEEFF\">";
              }
            else
              {
                echo "  <tr>";
              }
        echo("<tr><td>No clients in database</td></tr>");  
        echo "    <td><input type=\"text\" name=\"client_ip\" size=\"24\"></td>";
        echo "    <td>&nbsp;</td>";
        echo "    <td><input type=\"text\" name=\"beamline\" size=\"3\"></td>";
        echo "    <td>&nbsp;</td>";
        echo "    <td><input type=\"submit\" value=\"Add Client\" name=\"submit\"></td>";
        echo "  </tr>";
        echo "</FORM>";
        $j++; 
?>
      </tr>
    </table>
<? 
      }
?>

</body>
