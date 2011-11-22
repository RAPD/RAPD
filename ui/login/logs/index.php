<?php

  session_start();

  include("../config.php");
  include("../functions.php");

  if (allow_access(Administrators) != "yes")
  {
    header("Location:../login.html");
  }

?>

<html>

<head>
<meta http-equiv="Content-Type" content="text/html; charset=windows-1252">
<title>Log Viewer</title>
</head>

<frameset cols="170,*">
	<frame name="contents" target="main" src="log.html">
	<frame name="main" src="log.php">
	<noframes>
	<body>

	<p>This page uses frames, but your browser doesn't support them.</p>

	</body>
	</noframes>
</frameset>

</html>
