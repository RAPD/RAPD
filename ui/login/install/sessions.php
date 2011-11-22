<?
session_start(install);

echo $_SESSION[dbase_name];
echo $_SESSION[dbase_server];
echo $_SESSION[dbase_username];
echo $_SESSION[dbase_password];
echo $_SESSION[table_name];
echo $_SESSION[install_dir];

?>