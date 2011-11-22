<?php

$target_path = "./uploads/";
echo($target_path."\n");

$target_path = $target_path . basename( $_FILES['uploadedfile']['name']); 
echo($target_path."\n");

if(move_uploaded_file($_FILES['uploadedfile']['tmp_name'], $target_path)) {
    echo "The file ".  basename( $_FILES['uploadedfile']['name']). 
    " has been uploaded";
} else{
    echo "There was an error uploading the file, please try again!";
}

?>
