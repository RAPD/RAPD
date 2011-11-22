<?

//set up the names of the database and table
$db_name ="rapd_users";
$table_name ="authorize";

//connect to the server and select the database
$server = "rapd.nec.aps.anl.gov";
$dbusername = "rapd";
$dbpassword = "dbpassword";

//domain information
$domain = "rapd.nec.aps.anl.gov";

//Change to "0" to turn off the login log
$log_login = "1";

//base_dir is the location of the files, ie http://www.yourdomain/login
$base_dir = "https://rapd.nec.aps.anl.gov/rapd/login";

//length of time the cookie is good for - 7 is the days and 24 is the hours
//if you would like the time to be short, say 1 hour, change to 60*60*1
$duration = time()+(60*60*24*30);

//the site administrator\'s email address
$adminemail = "fmurphy@anl.gov";

//sets the time to EST
$zone=3600*-6;

//do you want the verify the new user through email if the user registers themselves?
//yes = "0" :  no = "1"
$verify = "0";

//default redirect, this is the URL that all self-registered users will be redirected to
$default_url = "https://rapd.nec.aps.anl.gov/rapd/main.php";

//minimum and maximum password lengths
$min_pass = 8;
$max_pass = 20;


$num_groups = 0+2;
$group_array = array("Users","Administrators");

?>
