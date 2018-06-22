var express = require("express");
var router = express.Router();
const jwt = require("jsonwebtoken");
var mongoose = require("../models/mongoose");
const multer = require("multer");

// Configuration
const config = require("../config"); // get our config file

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
var upload = multer({
  dest: config.upload_directory,
  rename: function(fieldname, filename) {
    return filename + Date.now();
  },
  onFileUploadStart: function(file) {
    console.log(file.originalname + " is starting ...");
  },
  onFileUploadComplete: function(file) {
    console.log(file.fieldname + " uploaded to  " + file.path);
  }
});


router
  .route("/upload_mx_raw")
  .post(upload.any(), function(req, res) {
    
    console.log(req.decoded._doc);
    console.log(req.files);
    
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
  // upload(req, res, function (err) {
  //   if (err) {
  //     return res.end(err.toString());
  //   }

  res.end("File is uploaded");
  // });
});

// Export
module.exports = router;
