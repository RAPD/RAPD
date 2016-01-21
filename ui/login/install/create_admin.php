<?

session_start(install);

include ('../config.php');

?>

<html>

<head>
<meta http-equiv="Content-Language" content="en-us">
<meta http-equiv="Content-Type" content="text/html; charset=windows-1252">
<title>Create Your Administrator Accoun</title>
</head>

<body>

<p><b><font face="Tahoma" size="2">Create Your Administrator Account:</font></b></p>
<form method="POST" action="install_3.php">
	<table border="1" id="table1">
		<tr>
			<td><font face="Tahoma" size="2">First Name:</font></td>
			<td>
			<input type="text" name="first_name" size="20" style="font-family: Tahoma"></td>
		</tr>
		<tr>
			<td><font face="Tahoma" size="2">Last Name:</font></td>
			<td>
			<input type="text" name="last_name" size="20" style="font-family: Tahoma"></td>
		</tr>
		<tr>
			<td><font face="Tahoma" size="2">Username:</font></td>
			<td>
			<input type="text" name="user_name" size="20" style="font-family: Tahoma"></td>
		</tr>
		<tr>
			<td><font face="Tahoma" size="2">Password:</font></td>
			<td>
			<input type="text" name="password" size="20" style="font-family: Tahoma"></td>
		</tr>
		<tr>
			<td><font face="Tahoma" size="2">Redirect To:</font></td>
			<td>
			<input type="text" name="redirect_to" size="50" value="<?php echo $_SESSION[install_dir]; ?>/admin/adminpage.php" style="font-family: Tahoma"></td>
		</tr>
		<tr>
			<td>&nbsp;</td>
			<td>&nbsp;</td>
		</tr>
		<tr>
			<td>
			<input type="submit" value="Submit" name="B1" style="font-family: Tahoma; font-size: 10pt"></td>
			<td>&nbsp;</td>
		</tr>
	</table>
</form>

</body>

</html>