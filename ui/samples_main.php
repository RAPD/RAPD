<?php

//prevents caching
header("Expires: Sat, 01 Jan 2000 00:00:00 GMT");
header("Last-Modified: ".gmdate("D, d M Y H:i:s")." GMT");
header("Cache-Control: post-check=0, pre-check=0",false);
session_cache_limiter();
session_start();

require('./login/functions.php');

if(allow_user() != "yes")
{
    include ('./login/no_access.html');
    exit();
}
?>

<head>
  <meta http-equiv="Content-Language" content="en-us">
  <title>RAPD Samples</title>
  <link rel="shortcut icon" href="./css/favicon.ico" type="image/x-icon">
    <!-- jquery UI styling -->
    <link type="text/css" href="css/south-street/njquery-ui-1.7.2.custom.css" rel="stylesheet" />
    <!-- done with image viewer css -->
    <link type="text/css" href="css/rapd.css"                                rel="stylesheet" />

    <!-- Load up the javasript using google to make it faster remotely -->
    <script src="http://www.google.com/jsapi"></script>
  <script>
    google.load("jquery", "1.4.2");
    google.load("jqueryui", "1.7.2");
  </script>
</head>
<body class='banner'>
  <h1>RAPD Samples</h1>

<script id="source" language="javascript" type="text/javascript">
$(function() {
    $('#upload').dialog({ autoOpen: false,
			    height: 400,
			     width: 700,
                             modal: true,
       });
    $('#opendialog').click(function() {
       $('#upload').dialog('open');
       return false;
   });
  });
</script>

<noscript>
    <h1 align="center"><font color="#FF0000">Javascript is required to view this page.</font></h1>
</noscript>

<div class="clear" style="margin-bottom: 26px;">
  <table align='center'>
    <tr>
      <td>
        <a class="button" href="samples_all.php" onclick="this.blur(); return true;"><span>Samples</span></a>
      </td>
      <td>
<?php 
    if (allow_access(Administrators) == "yes")
    {
      echo('        <a class="button" href="link_samples_trip.php" onclick="this.blur(); return true;"><span>Link Samples</span></a>');
      echo('      </td>');
      echo('      <td>');
    }
?>

        <a class="button" href="#" id="opendialog" onclick="this.blur(); return true;"><span>Upload Spreadsheet</span></a>
      </td>
      <td>
        <a class="button" href="http://lilith.nec.aps.anl.gov/~perry/necat-sample-sheet.xls" onclick="this.blur(); return true;"><span>Download Spreadsheet Template</span></a>
      </td>
      <td>
        <a class="button" href="main.php" onclick="this.blur(); return true;"><span>Main Page</span></a>
      </td>
    </tr>
  </table>
</div>
<div width="100" id="upload" title="Upload Spreadsheet">
<h2 style="text-align: left;">Instructions:</h2>
<OL style="text-align: left;">
<li>One puck per sheet in the spreadsheet.
<li>Only 16 samples per puck.
<li>Puck ID must be unique.
<li>Puck ID and Crystal ID must be less than 15 characters. Spaces will be replaced by an underscore.
<li>Spreadsheet name must be unique.  Spaces will be replaced by an underscore.
</OL>
</p>
<form enctype="multipart/form-data"
      method="post"
      action="../../cgi-bin/import_spreadsheet.py">
<h2>Select spreadsheet to be uploaded</h2>
<p><input type=file size=50 name=spreadsheet>
<?php 
    if (allow_access(Administrators) == "yes")
    {
      echo('<br>           Choose User: <select name="username">');

      require ("./login/config.php");

      //make the connection to the database
      $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
      $db = @mysql_select_db($db_name,$connection)or die(mysql_error());

      //build and issue the query
      $sql ="SELECT username FROM authorize GROUP BY username";
      $result = @mysql_query($sql,$connection) or die(mysql_error());
      while ($sql = mysql_fetch_object($result))
        {
           $uname = $sql -> username;
           if ($uname == $_SESSION[username]) 
	     {
	       echo "<option value=\"$uname\" selected=\"$uname\">$uname</option>";
	     } else {
               echo "<option value=\"$uname\">$uname</option>";
           }
        }
      echo('                      </select>');
    } else {
      echo('           <input type=hidden name=username value="'.$_SESSION[username].'">');
    }

?>
 
<p><input type=submit value=Upload>
</form>

</div>
</body>
</html>
