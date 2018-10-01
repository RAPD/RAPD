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
router
  .route("/upload_mx_raw/:project_id")
  .post(upload.any(), function(req, res, next) {
    console.log("req.files", req.files);
    console.log("req.decoded >>", req.decoded);
    /*
    { groups: [ { groupname: 'NE-CAT', _id: '55e4ffd2fc6a5017ada7efe2' } ],
      loginAttempts: 0,
      pass_force_change: false,
      role: 'site_admin',
      status: 'active',
      _id: '55e4ffd3fc6a5017ada7f5db',
      group_id: '55e4ffd2fc6a5017ada7efe2',
      surname: 'Murphy',
      name: 'Frank Murphy',
      created: '2011-06-02T14:35:02.000Z',
      type: 'admin',
      id: 1,
      sms: '(630) 930-2968',
      modified: '2017-05-31T15:32:48.548Z',
      pass_rename: 0,
      phone: '(630) 930-2968',
      group_id_old: 1,
      last_login: '2018-09-12T19:41:24.833Z',
      pass: '$2a$10$r2uf0nJYgtvPQlOQgwEU5.fUR.tDburvtXOhiHvS5NaRz0sbFo02u',
      salt: 'ejpO5ew-4)7vWiTk97K=bIC6!u(U1JaV&WKXyYoP',
      timezone: 0,
      shortname: 'frank',
      pass_expire: '2019-07-31T13:45:51.591Z',
      email: 'fmurphy@anl.gov',
      creator: '55e4ffd3fc6a5017ada7f5db',
      username: 'Frank Murphy',
      timestamp: '2018-07-30T08:27:55.460Z',
      iat: 1537988579,
      exp: 1538074979 }
    */
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
      /* found_file example
      { _id: 5babccbdceea260f496e5fb0,
        filename: 'thaum1_01s-01d_1_mergable.mtz',
        contentType: 'binary/octet-stream',
        length: 10972392,
        chunkSize: 261120,
        uploadDate: 2018-09-26T18:15:26.780Z,
        aliases: null,
        metadata:
        { description: null,
          hash: '4dcdcd090364522ebaf268c96d90f7df8ea91de8',
          project_id: null,
          result_id: null,
          file_type: null },
        md5: '4a65ca59fe3cf3f89bf2645002f2e87d' }
      */

      // Error in looking for file
      if (err) {
        console.error(err.toString());
        return res.end(err.toString());
        // No error
      } else {
        // file will be null if not found
        console.log("found_file >>", found_file);

        // No file with this hash - store it
        if (!found_file) {
          // Construct metadata for file
          let metadata = {
            description: "Raw upload",
            hash: hash,
            originalname: file.originalname,
            project_id: req.params.project_id,
            result_id: null,
            file_type: null
          };

          // Create writestream
          var writestream = gridfs.createWriteStream({
            filename: file.originalname,
            metadata: metadata
          });

          // Writestream events - open, close, error (finish, drain, pipe, unpipe)
          writestream.on("open", function(file) {
            // do something with `file`
            console.log("writestream open", file);
          });
          writestream.on("close", function(file) {
            // do something with `file`
            console.log("writestream closed", file);

            /* file example
            { _id: 5bad0a6aee7d9014bdf17e5d,
              filename: 'thaum1_01s-01d_1_mergable.mtz',
              contentType: 'binary/octet-stream',
              length: 10972392,
              chunkSize: 261120,
              uploadDate: 2018-09-27T16:51:18.810Z,
              aliases: undefined,
              metadata:
              { description: 'Raw upload',
                hash: '4dcdcd090364522ebaf268c96d90f7df8ea91de8',
                originalname: 'thaum1_01s-01d_1_mergable.mtz',
                project_id: '5ba538d643266b24a16e31c6',
                result_id: null,
                file_type: null },
              md5: '4a65ca59fe3cf3f89bf2645002f2e87d' }
            */

            // Make sure this is a file RAPD understands
            // Construct command
            let command = {
              "command":"GETFILETYPE",
              "data": {
                "originalname": file.metadata.originalname,
                "file_id": file._id
              }
            };
            // Listen for result

            // Push command to the launcher
            console.log("RAPD_JOBS", JSON.stringify(command));
            // redis.lpush("RAPD_JOBS", JSON.stringify(command))

            // Add to project

            // Send info to client
            res.end(JSON.stringify({
              status: True,
              file: file,
              message: "File uploaded"
            }));
          });
          writestream.on("error", function(err) {
            console.error(err);
            res.send(500, err);
          });

          // Stream file (buffer) to database
          const readable = new Readable();
          readable._read = () => {}; // _read is required but you can noop it
          readable.push(file.buffer);
          readable.push(null);
          readable.pipe(writestream);

          // Already had this upload
        } else {
          // res.end("File already uploaded");
          res.end(
            JSON.stringify({
              status: false,
              file: found_file,
              message: "File already uploaded"
            })
          );
        }
      }
    });

    // Notify the user that all is well
    // res.end("File is uploaded");

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
