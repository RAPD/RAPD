<?php

//prevents caching
header("Expires: Sat, 01 Jan 2000 00:00:00 GMT");
header("Last-Modified: ".gmdate("D, d M Y H:i:s")." GMT");
header("Cache-Control: post-check=0, pre-check=0",false);
session_cache_limiter();
session_start();

require('./login/config.php');
require('./login/functions.php');

//this is group name or username of the group or person that you wish to allow access to
// - please be advise that the Administrators Groups has access to all pages.
if (allow_access(Administrators) != "yes")
{
    include ('./login/no_access.html');
    exit;
}

if(allow_user() != "yes")
{
    include ('./login/no_access.html');
    exit();
}
?>

<head>
  <meta http-equiv="Content-Language" content="en-us">

  <link type="text/css" href="css/ndemo_table.css"  rel="stylesheet" />
  <link type="text/css" href="css/ndemo_page.css"   rel="stylesheet" />
  <link type="text/css" href="css/south-street/njquery-ui-1.7.2.custom.css" rel="stylesheet" />
  <link type="text/css" href="css/rapd.css"         rel="stylesheet" /> 

  <title>RAPD</title>
  <link rel="shortcut icon" href="./css/favicon.ico" type="image/x-icon">

</head>

<body class='banner'>
<h1>RAPD Trips</h1>

  <table border="0" width="100%" id="table1">
    <tr valign="top">
      <td>
        <table>
          <tr>
            <td><b>Logged in as <?php echo $_SESSION[username]; ?></b></td>
          </tr>
          <tr>
            <td><i><a href="main.php">Go to Main Page</a></i></td>
          </tr>
          <tr>
            <td><i><a href="./login/admin/adminpage.php">Go to Administrative Control Panel</a></i></td>
          </tr>
          <tr>
            <td><i><a href="./login/logout.php">Logout</a></i></td>
          </tr>
        </table>
    </td>
    <td>
<!--    </tr>
  </table> -->
<?php

//make the connection to the database
$connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
$db = @mysql_select_db($db_name,$connection)or die(mysql_error());

//build and issue the query
$sql ="SELECT * FROM trips ORDER BY trip_finish DESC";
$result = @mysql_query($sql,$connection) or die(mysql_error());

$num = mysql_num_rows($result);

if ($num > 0)
{
    echo('<div id="auto_wrapper" class="dataTables_wrapper">');
    echo "  <table id='trip_table' class='ranking'>\n";
    //the counter for row coloring
    echo "      <thead>\n";	
    echo "        <tr>\n";
    echo "          <th class='sorting'>User</th>\n";
    echo "          <th class='sorting'>Start Date</th>\n";
    echo "          <th class='sorting'>End Date</th>\n";
    echo "          <th class='sorting'>Trip_ID</th>\n";
    echo "          <th class='sorting'>Root Data Dir</th>\n";
    echo "          <th class='sorting'>Beamline</th>\n";
    echo "          <th class='sorting'>Select</th>\n";
    echo "        </tr>\n";
    echo "      </thead>\n";
    echo "      <tbody>\n";
	while ($sql = mysql_fetch_object($result))	
	{
	    $start    = $sql -> trip_start;
            $finish   = $sql -> trip_finish;
    	    $data     = $sql -> data_root_dir;
            $beamline = $sql -> beamline;
            $user     = $sql -> username;
            $trip_id  = $sql -> trip_id;
	
            echo "    <tr>\n";	
            echo "      <td>$user</td>\n";
            echo "      <td>$start</td>\n";
	    echo "      <td>$finish</td>\n";
	    echo "      <td>$trip_id</td>\n";
            echo "      <td>$data</td>\n";
	    echo "      <td align='center'>$beamline</td>\n";
            echo "      <td align='center'>\n";
            echo "        <form method=\"POST\" action=\"trip_data_main.php\">\n";
            echo "          <input type=\"hidden\" name=\"user\" value=\"$user\"> \n";
            echo "          <input type=\"hidden\" name=\"trip_id\" value=\"$trip_id\">\n";
            echo "          <input type=\"hidden\" name=\"data\" value=\"$data\">\n";
            echo "          <input type=\"hidden\" name=\"beamline\" value=\"$beamline\">\n";
            echo "          <input type=\"submit\" value=\"View Trip\" name=\"submit\">\n";
            echo "        </form>\n";
            echo "      </td>\n";
	    echo "    </tr>\n";
	}
        echo "</tbody>\n";
	echo "</table>";
}
else
{
	echo "<P>No trips in database</p>";
}
?>
  </div>
</td>
</tr>
</table>
	<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.4.4/jquery.min.js"></script>
  <script src="http://ajax.googleapis.com/ajax/libs/jqueryui/1.8.9/jquery-ui.min.js"></script>
  <!--<script type="text/javascript" language="javascript" src="./js/jquery-1.5.1.min.js">    </script>
	<script type="text/javascript" language="javascript" src="./js/jquery-ui-1.8.11.min.js">    </script> -->
  <script type="text/javascript" language="javascript" src="./js/jquery.dataTables.min.js">    </script>
  <script type='text/javascript'>
    $(document).ready(function() {
        tripTable = $('#trip_table').dataTable({
                    "aaSorting": [[ 2, "desc" ]],
                    "aoColumns": [ null,
                                   null,
                                   null,
                                   {"bVisible":false},
                                   null,
                                   null,
                                   null],
                    "bJQueryUI": true,
                    "iDisplayLength": 50
        });
    } );
		</script>
</body>
