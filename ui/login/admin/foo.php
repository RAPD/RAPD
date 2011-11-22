<?php

rmdir_recursive("./tester_dir");

function rmdir_recursive($dir) 
{          
  // List the contents of the directory table        
  $dir_content = scandir($dir);          
  // Is it a directory?             
  if ($dir_content != FALSE)
  {
    // For each directory entry                    
    foreach($dir_content as $entry)                            
    {                            
      // Unix symbolic shortcuts, we go                            
      if (! in_array($entry, array('.','..')))
      {
        // We find the path from the beginning                         
        $entry = $dir.'/'.$entry;                             
        // This entry is not an issue: it clears                
        if (! is_dir($entry))  
        {  
          unlink($entry);  
        } 
        // This entry is a folder, it again on this issue 
        else 
        { 
          rmdir_recursive($entry);  
        }                                 
      }                       
    }
  }
  // It has erased all entries in the folder, we can now erase 
  rmdir($dir);  
}

?>
