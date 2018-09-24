var express = require("express");
var router = express.Router();
const jwt = require("jsonwebtoken");
var mongoose = require("../models/mongoose");
const multer = require("multer");
const ioredis = require("ioredis");

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

router.route("/upload_mx_raw").post(upload.any(), function(req, res, next) {

  console.log("req.files", req.files);

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
