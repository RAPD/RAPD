from pymongo import MongoClient


if __name__ == "__main__":
    print "RAPD MongoDB setup script"
    print ""
    print "This script is designed to set up RAPD on a brand new MongoDB instance. If this is not the case you are currently out of luck"""

    # Get connection info
    host = raw_input("Enter Mongo host [127.0.0.1]: ")
    if host == "":
        host = "127.0.0.1"
    port = raw_input("Enter Mongo port [27017]: ")
    if port == "":
        port = 27017
    else:
        port = int(port)
    print host, port

    # Create client
    client = MongoClient(host, port)

    # Create rapd database
    db = client['rapd']
    
    # Create collections
    if ("activities" in db.collection_names()):
        print "activities collection already exists"
    else:    
        print "Creating activities collection"
        collection = db.activities


    """
    [
	"activities",
	"fs.chunks",
	"fs.files",
	"groups",
	"images",
	"login_attempts",
	"logins",
	"mx_analysis_results",
	"mx_index_results",
	"mx_integrate_results",
	"mx_mr_results",
	"mx_pdbquery_results",
	"pdbs",
	"plugin_processes",
	"plugin_results",
	"projects",
	"results",
	"resultss",
	"runs",
	"sessions",
	"users"
    ]
    """