<?php
//prevents caching
header("Expires: Sat, 01 Jan 2000 00:00:00 GMT");
header("Last-Modified: ".gmdate("D, d M Y H:i:s")." GMT");
header("Cache-Control: post-check=0, pre-check=0",false);
session_cache_limiter();

session_start();

//require the config file
require ("../config.php");
require ("../functions.php");

if ($page == ""){$page = 1;}
	
//check for authority to view this page
if (allow_access(Administrators) != "yes")
  {
    echo "You are not authorized to perform this function";
    exit;
  }
?>

<head>
<meta http-equiv="Content-Language" content="en-us">

<style type="text/css" media="screen">
  @import url("../../css/rapd.css");
</style>
</head>
<body class='banner' topmargin="0" leftmargin="10" rightmargin="0" bottommargin="0">
  <h1>RAPD Trip Administration</h1>

<?php
//check required fields
if ($_POST[data] == "")
  {
    if ($_POST[data1] == "")
    {
        echo "<P>Root Data Dir is blank, please try again.</p>";
        echo "<P><a href=\"../../main.php\">Main Page</a></P>";
        echo "<P><a href=\"trips.php\">Back to trips</a></p>";
        echo "<P><a href=\"adminpage.php\">Back to the administrative control panel</a></p>";
        exit;
    }
  }


//edit the data root dir to not have any leading spaces and not end in a /
if ($_POST[data] != "")
{
    $drd_tmp = ltrim($_POST[data]);
    $drd = rtrim($drd_tmp," \/");
    $bline = $_POST[beamline];
    $delete = 0;
} elseif ($_POST[data1])
{
    $drd_tmp = ltrim($_POST[data1]);
    $drd = rtrim($drd_tmp," \/");
    $bline = $_POST[beamline1];
    $delete = 1;
}


//make the connection to the database
$connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
$db = @mysql_select_db($db_name,$connection)or die(mysql_error());

//make query to database
$sql ="SELECT * FROM trips WHERE username='$_SESSION[username1]' AND data_root_dir='$drd'";
$result = @mysql_query($sql,$connection) or die(mysql_error());

//get the number of rows in the result set
$num = mysql_num_rows($result);

//check if that username already exists
if ($num != 0)
  {
      echo "<P>Sorry, that user already has a trip that claims the submitted data directory</P>";
      echo "<P><a href=\"../../main.php\">Main Page</a></P>";
      echo "<P><a href=\"trips.php\">Back to trips</a></p>";
      echo "<P><a href=\"adminpage.php\">Back to the administrative control panel</a></p>";
  }
else
  {
    $sql_add = "INSERT INTO trips (username,data_root_dir, beamline) VALUES ('$_SESSION[username1]', '$drd','$bline' )";
    $result = @mysql_query($sql_add,$connection) or die(mysql_error());

    //add the directory to the structure
    //get the unique trip id for the data directory name
    $sql = "SELECT * FROM trips WHERE data_root_dir='$drd'";
    $result = @mysql_query($sql,$connection) or die(mysql_error());
    $sql = mysql_fetch_object($result);
    $my_dir = $sql -> trip_id;
    //now make the directories
    mkdir("../../users/$_SESSION[username1]/$my_dir");
    mkdir("../../users/$_SESSION[username1]/$my_dir/single");
    mkdir("../../users/$_SESSION[username1]/$my_dir/pair");
    mkdir("../../users/$_SESSION[username1]/$my_dir/run");
    mkdir("../../users/$_SESSION[username1]/$my_dir/merge");
    mkdir("../../users/$_SESSION[username1]/$my_dir/download");
    mkdir("../../users/$_SESSION[username1]/$my_dir/structure");


 
    //now query the database to see if there are any orphans 
    //that could be assigned to this trip
    mysql_close($connection); 
    $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
    $db = @mysql_select_db('rapd_data',$connection)or die(mysql_error());    

    $sql = "SELECT * FROM orphan_results WHERE data_root_dir='$drd'";
    $result = @mysql_query($sql,$connection) or die(mysql_error());
    
    //count the number of rows that match
    $num = mysql_num_rows($result);     

    //we have at least one orphan result
    if ($num != 0)
      {
        while ($sql = mysql_fetch_object($result))
          {
            //grab the data from the table
            $orphan_id     = $sql -> orphan_result_id;
            $type          = $sql -> type;
            $data_root_dir = $sql -> data_root_dir;
            $result_id     = $sql -> result_id;
            $date          = $sql -> date;

            echo "<P>Orphan result: $type $data_root_dir $result_id $date</P>";

            //delete the result from orphan_results table
            $db = @mysql_select_db('rapd_data',$connection)or die(mysql_error());
            $sql2 = "DELETE FROM orphan_results WHERE orphan_result_id='$orphan_id'";
            $result2 = @mysql_query($sql2,$connection) or die(mysql_error());           

            //update the trip dates
            if ($date)
              {
                $db = @mysql_select_db('rapd_users',$connection)or die(mysql_error());
                $sql3 = "UPDATE trips SET trip_start='$date'  WHERE data_root_dir='$drd' AND (trip_start  IS NULL OR trip_start>'$date')";
                $result3 = @mysql_query($sql3,$connection) or die(mysql_error());
                $sql4 = "UPDATE trips SET trip_finish='$date' WHERE data_root_dir='$drd' AND (trip_finish IS NULL OR trip_finish<'$date')";
                $result4 = @mysql_query($sql4,$connection) or die(mysql_error());
              }

            //single result type
            if ($type == 'single')
              {
                //copy files here
                $source = "/var/www/html/rapd/users/orphans/single/";
                $dest = "/var/www/html/rapd/users/$_SESSION[username1]/$my_dir/single/";
                copy($source.$result_id."_short.php",$dest.$result_id."_short.php");
		copy($source.$result_id."_long.php",$dest.$result_id."_long.php");
		copy($source.$result_id."_plots.php",$dest.$result_id."_plots.php");
		copy($source.$result_id."_big.jpg",$dest.$result_id."_big.jpg");
		copy($source.$result_id."_small.jpg",$dest.$result_id."_small.jpg");
                copy($source.$result_id."_pyr_000_090.tif",$dest.$result_id."_pyr_000_090.tif");
                copy($source.$result_id."_pyr_100_090.tif",$dest.$result_id."_pyr_100_090.tif");
                copy($source.$result_id."_stac.php",$dest.$result_id."_stac.php");
              }
            elseif ($type == 'pair')
              {
                //copy files here
                $source = "/var/www/html/rapd/users/orphans/pair/";
                $dest   = "/var/www/html/rapd/users/$_SESSION[username1]/$my_dir/pair";
                copy($source.$result_id."_short.php",$dest.$result_id."_short.php");
                copy($source.$result_id."_long.php",$dest.$result_id."_long.php");
                copy($source.$result_id."_plots.php",$dest.$result_id."_plots.php");
                copy($source.$result_id."_big_1.jpg",$dest.$result_id."_big_1.jpg");
                copy($source.$result_id."_small_1.jpg",$dest.$result_id."_small_1.jpg");
                copy($source.$result_id."_big_2.jpg",$dest.$result_id."_big_2.jpg");
                copy($source.$result_id."_small_2.jpg",$dest.$result_id."_small_2.jpg");
                copy($source.$result_id."_pyr_000_090.tif",$dest.$result_id."_pyr_000_090.tif");
                copy($source.$result_id."_pyr_100_090.tif",$dest.$result_id."_pyr_100_090.tif");
                copy($source.$result_id."_pyr_200_090.tif",$dest.$result_id."_pyr_200_090.tif");
                copy($source.$result_id."_pyr_300_090.tif",$dest.$result_id."_pyr_300_090.tif");
                copy($source.$result_id."_stac.php",$dest.$result_id."_stac.php");
              }
            elseif ($type == 'run')
              {
                //copy files here
                $source = "/var/www/html/rapd/users/orphans/run/";
                $dest = "/var/www/html/rapd/users/$_SESSION[username1]/$my_dir/run";
                copy($source.$result_id."_xia2.log",$dest.$result_id."_xia2.log");
                copy($source.$result_id."_xscale.log",$dest.$result_id."_xscale.log");
                copy($source.$result_id."_scala.log",$dest.$result_id."_scala.log");
                copy($source.$result_id."_short.php",$dest.$result_id."_short.php");
                copy($source.$result_id."_plots.php",$dest.$result_id."_plots.php"); 
              }
          }

      }
    else
      {
        echo "<P>No orphan results in the database</P>";
      }

    //Now delete lines from candidate_dirs if we have pulled from there
    if ($delete == 1)
    {
    $db = @mysql_select_db('rapd_users',$connection)or die(mysql_error());
    $sql5 = "DELETE FROM candidate_dirs WHERE dirname='$drd'";
    $result5 = @mysql_query($sql5,$connection) or die(mysql_error());
    }


    //close connection to the database
    mysql_close($connection);

    echo "<P>Trip successfully added to database.</P>";
    echo "<P><a href=\"../../main.php\">Main Page</a></P>";
    echo "<P><a href=\"../../data_main.php\">View Data - User Perspective</a></P>";
    echo "<P><a href=\"../../data_admin.php\">View Data - Administrator Perspective</a></P>";
    echo "<P><a href=\"trips.php\">Back to trips</a></p>";
    echo "<P><a href=\"adminpage.php\">Back to the administrative control panel</a></p>";
  }
?>
</body>
