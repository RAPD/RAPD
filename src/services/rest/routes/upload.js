var express = require("express");
var router = express.Router();
const jwt = require("jsonwebtoken");
var mongoose = require("../models/mongoose");
const multer = require("multer");
var Grid = require("gridfs-stream");

const crypto = require('crypto');
const fs = require("fs");
// const shasum = require("shasum");

// Configuration
const config = require("../config"); // get our config file

// Setting up gridfs
Grid.mongo = mongoose.mongo;

// Redis
const Redis  = require('ioredis');
var redis_client = new Redis(config.redis_connection);

// For calculating hashes
function fileHash(filename, algorithm = 'sha1') {
  return new Promise((resolve, reject) => {
    // Algorithm depends on availability of OpenSSL on platform
    // Another algorithms: 'sha1', 'md5', 'sha256', 'sha512' ...
    let shasum = crypto.createHash(algorithm);
    try {
      let s = fs.ReadStream(filename)
      s.on('data', function (data) {
        shasum.update(data)
      })
      // making digest
      s.on('end', function () {
        const hash = shasum.digest('hex')
        return resolve(hash);
      })
    } catch (error) {
      return reject('calc fail');
    }
  });
}

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
    console.log('Starting ' + file.name);
  },
  onFileUploadComplete: function(file) {
    console.log(file.fieldname + " uploaded to  " + file.path);
  },
  onFileUploadData : function (file, data) {
    console.log('Recieving Data');
  },
  onFileUploadComplete : function (file) {
    console.log('Completed file!');
  },
  onParseStart : function () {
    console.log('Starting to parse request!');
  },
  onParseEnd : function (req, next) {
    console.log('Done parsing!');
    next();
  },
  onError : function (e, next) {
    if (e) {
      console.log(e.stack);
    }
    next();
  }
});


router
  .route("/upload_mx_raw")
  .post(upload.any(), function(req, res) {
  // .post(function(req, res) {

    // console.log(req.headers.referer);
    // console.log(req.decoded);
    console.log(req.files);

    const project_id = req.headers.referer.split("/").slice(-1)[0];

    fileHash(req.files[0].path).then((hash) => {
      // Put the metadata together    
      const metadata = {
        description: "manual upload",
        hash: hash,
        originalname: req.files[0].originalname,
        path: req.files[0].path,
        project_id: project_id,
        result_id: null,
        file_type: null
      };
      console.log(metadata);

      // Diffraction data
      if (metadata.originalname.endsWith(".mtz")) {
        
        console.log("DIFFRACTION DATA");

        // Create request
        const request = {
          command: "ASSESS_INTEGRATED_DATA",
          data: req.files[0].path,
          preferences: {
            analysis: true,
            data_file: metadata.path,
            import: true,
            json: true,
            no_color: true,
            pdbquery: false,
            progress: false,
            run_mode: "server",
            show_plots: false,
            site: null,
            test: false,
            verbose: false
          },
          process: {
            image_id: null,
            parent_id: null,
            project_id: project_id,
            repr: metadata.originalname,
            run_id: null,
            session_id: null,
            status: 0,
            type: "plugin",
          },
          site_parameters: false,
        };

        console.log("REQUEST", request);

        // redis_client.lpush('RAPD_JOBS', JSON.stringify(request), function(err, queue_length) {
        //   if (err) {
        //     console.error(err);
        //     res.status(500).json({
        //       success: false,
        //       error: err
        //     });
        //   } else {
        //     console.log('Job added to RAPD_JOBS queue length:', queue_length);
        //     res.status(200).json({
        //       success: true,
        //       queue_length: queue_length
        //     });
        //   }
        // });

      }

    });

    

    

    
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
