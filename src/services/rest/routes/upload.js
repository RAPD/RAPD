var express = require("express");
var router = express.Router();
const jwt = require("jsonwebtoken");
var mongoose = require("../models/mongoose");
const multer = require("multer");

// Configuration
const config = require("../config"); // get our config file

// MongoDB Models
const Pdb = mongoose.ctrl_conn.model("Pdb", require("../models/pdb").PdbSchema);
const Session  = mongoose.ctrl_conn.model('Session', require('../models/session').SessionSchema);


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
    
    console.log(req.decoded);
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

router
  .route("/upload_pdb")
  .post(upload.any(), function(req, res) {
    
    // console.log(req);
    // console.log(req.decoded);
    // console.log(req.files);
    
    // Fing the group that belongs to the session
    Session.findOne({_id:req.body.session_id}, function(err, session){

      // console.log(session);

      // Save a record of where the file is
      let new_pdb = new Pdb({
        filename:req.files[0].filename,
        group:session.group,
        originalname:req.files[0].originalname,
        path:req.files[0].path,
        session:req.body.session_id,
        uploader:req.decoded._id,
      });

      new_pdb.save(function(err, return_pdb) {
        if (err) {
          console.error(err);
          res.send(err);
        } else {
          console.log('Pdb uploaded successfully', return_pdb);
          res.json({
            success:true,
            operation:'upload',
            pdb:return_pdb,
          });
        }
      });
    })

    

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

  // res.end("File is uploaded");
  // });
});

// Export
module.exports = router;
