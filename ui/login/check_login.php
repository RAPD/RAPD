<?

session_start();

//check to see if the user already has an open session
if (($_SESSION[username] != "") && ($_SESSION[password] != ""))
{
	header("Location:$_SESSION[redirect]");
	exit;
}

//check to see if cookies have been set previously
if(($lr_user != "") && ($lr_pass != ""))
{
	header("Location:redirect.php");
	exit;
}

//if neither is true, redirect to login
	header("Location:login.html");


?>
