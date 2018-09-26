var express = require("express");
var router = express.Router();
const ioredis = require("ioredis");
const jwt = require("jsonwebtoken");
var mongoose = require("../models/mongoose");
const multer = require("multer");
const sha1 = require("sha1");
const { Readable } = require("stream");

var Grid = require("gridfs-stream");
Grid.mongo = mongoose.mongo;

// Configuration
const config = require("../config"); // get our config file

// Connect to redis
try {
  var redis = new ioredis(config.redis_connection);
} catch (e) {
  console.error("Cannot connect to redis", config.redis_connection);
  throw e;
}

// MongoDB Models
// const Project = mongoose.ctrl_conn.model(
//   "Project",
//   require("../models/project").ProjectSchema
// );
// const Result = mongoose.ctrl_conn.model(
//   "Result",
//   require("../models/result").ResultSchema
// );
// const Session = mongoose.ctrl_conn.model(
//   "Session",
//   require("../models/session").SessionSchema
// );

// Middleware for uploads
var storage = multer.memoryStorage();
var upload = multer({
  dest: config.upload_directory,
  storage: storage,
  rename: function(fieldname, filename) {
    return filename + Date.now();
  },
  onFileUploadStart: function(file) {
    console.log(file.originalname + " is starting ...");
  },
  onFileUploadComplete: function(file) {
    console.log(file.fieldname + " is complete ...");
  }
});

// Updload data
router.route("/upload_mx_raw/:project_id").post(upload.any(), function(req, res, next) {
  
  console.log("req.files", req.files);
  console.log("req.decoded >>", req.decoded);
  console.log("req.params.project_id >>", req.params.project_id);

  // req.files example
  // [ { fieldname: 'file',
  //   originalname: 'thaum1_01s-01d_1_mergable_min_rfree.mtz',
  //   encoding: '7bit',
  //   mimetype: 'application/octet-stream',
  //   destination: '/tmp',
  //   filename: '60663de62aceed9752482725a8b69901',
  //   path: '/tmp/60663de62aceed9752482725a8b69901',
  //   size: 2528960 } ]

  // Break out the file
  let file = req.files[0];

  // Get the hash of the file
  let hash = sha1(file.buffer);
  // console.log("hash", hash);

  // Check if file in database
  // Connect to GridFS
  var gridfs = Grid(mongoose.ctrl_conn.db);

  // See if there is a file with this hash
  gridfs.files.findOne({ "metadata.hash": hash }, function(err, found_file) {
    // Error
    if (err) {
      console.error(err.toString());
      return res.end(err.toString());
      // No error
    } else {
      // file will be null if not found
      console.log("found_file >>", found_file);

      // No file with this hash - store it
      // metadata for file
      let metadata = {
        description: null,
        hash: hash,
        project_id: req.params.project_id,
        result_id: null,
        file_type: null
      };
      /* metadata example again from python
      metadata={"description":data.get("description", "archive"),
                "hash":data.get("hash"),
                "result_id":_result_id,
                "file_type":file_type})
      */

      // Create write stream
      var writestream = gridfs.createWriteStream({
        filename: file.originalname,
        metadata: metadata
      });

      writestream.on("open", function(file) {
        // do something with `file`
        console.log("writestream open", file);
      });

      writestream.on("close", function(file) {
        // do something with `file`
        console.log("writestream closed", file);
      });

      // Stream file (buffer) to database
      const readable = new Readable();
      readable._read = () => {}; // _read is required but you can noop it
      readable.push(file.buffer);
      readable.push(null);
      readable.pipe(writestream);
    }

    // var readstream = gridfs.createReadStream({
    //   _id: file._id
    // });
    // req.on("error", function(err) {
    //   console.error(err);
    //   res.send(500, err);
    // });
    // readstream.on("error", function(err) {
    //   console.error(err);
    //   res.send(500, err);
    // });
    // console.log("Success");
    // readstream.pipe(res);
  });

  /* SOME PYTHON FOR EXAMPLE
  # See if we already have this file
  file_in_database = db.fs.files.find_one({"metadata.hash":metadata["hash"]})

  # File already saved
  if file_in_database:
      # Overwrite
      if replace:
          self.logger.debug("Overwriting file")
          # Open the path
          with open(path, "r") as input_object:
              file_id = grid_bucket.upload_from_stream(filename=os.path.basename(path),
                                                        source=input_object,
                                                        metadata=metadata)
      # Do not overwrite
      else:
          self.logger.debug("Not overwriting file")
          file_id = file_in_database["_id"]
  # New file
  else:
      self.logger.debug("Writing new file")
      # Open the path
      with open(path, "r") as input_object:
          file_id = grid_bucket.upload_from_stream(filename=os.path.basename(path),
                                          source=input_object,
                                          metadata=metadata)
  
  return file_id
  */

  // Notify the user that all is well
  res.end("File is uploaded");

  // req.files example
  // [ { fieldname: 'file',
  //   originalname: 'thaum1_01s-01d_1_mergable_min_rfree.mtz',
  //   encoding: '7bit',
  //   mimetype: 'application/octet-stream',
  //   destination: '/tmp',
  //   filename: '60663de62aceed9752482725a8b69901',
  //   path: '/tmp/60663de62aceed9752482725a8b69901',
  //   size: 2528960 } ]

  // var token = req.headers.authorization.replace("Bearer ", "");
  // console.log(token);
  // // decode token
  // if (token) {
  //   // Verifies secret and checks exp
  //   jwt.verify(token, app.get("superSecret"), function(err, decoded) {
  //     if (err) {
  //       return res.json({
  //         success: false,
  //         message: "Failed to authenticate token."
  //       });
  //     } else {
  //       console.log("DECODED", decoded);
  //       // let now = Date.now()/1000;
  //       // // if everything is good, save to request for use in other routes
  //       // if (decoded.iat <= now && decoded.exp >= now) {
  //       //   req.decoded = decoded;
  //       //   next();
  //       // }
  //     }
  //   });
  // }

  // upload.array(req, res, function(err) {
  //   if (err) {
  //     console.error(err.toString());
  //     return res.end(err.toString());
  //   } else {
  //     console.log("No error");
  //     // Notify the user that all is well
  //     res.end("File is uploaded");
  //   }

  // req.files [ { fieldname: 'file',
  // originalname: 'thaum1_01s-01d_1_mergable_min_rfree.mtz',
  // encoding: '7bit',
  // mimetype: 'application/octet-stream',
  // buffer: <Buffer 4d 54 5a 20 b5 a1 09 00 44 41 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 ... >,
  // size: 2528960 } ]

  // Store the file into the database
  // get the hash
  // console.log("1");
  // var digest = crypto.createHash("sha1")
  //   .update(req.files[0].buffer, "utf8")
  //   .digest("hex");

  // console.log("digest", digest);
  // console.log("2");

  // Now add the file to the project

  // Make sure this is a file RAPD understands
  // Construct command
  // let command = {
  //   "command":"GETFILETYPE",
  //   "data": {
  //     "filename": ""
  //   }
  // };
  // Listen for result

  // Push command to the launcher
  // redis.lpush("RAPD_JOBS", JSON.stringify(command))

  // console.log("req.files", req.files);

  // Launch an initial analysis

  // });
});

// Export
module.exports = router;
