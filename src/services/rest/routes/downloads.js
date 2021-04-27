var fs = require("fs");
var stream = require("stream");
var express = require("express");
var router = express.Router();
var mongoose = require("../models/mongoose");
var Grid = require("gridfs-stream");
// var toString = require('stream-to-string');

Grid.mongo = mongoose.mongo;

// const Group = require('../models/group');
// const Activity = require('../models/activity');
// const Session  = require('../models/session');
// const Result   = require('../models/result');

// on routes that end in /results
// ----------------------------------------------------
router
  .route("/download_by_id/:id")

  // Get a file for download
  .get(function(req, res) {
    console.log("download_by_id", req.params.id);

    // console.log(mongoose.ctrl_conn.db);
    var gridfs = Grid(mongoose.ctrl_conn.db);

    var readstream = gridfs.createReadStream({
      _id: req.params.id
    });
    req.on("error", function(err) {
      console.error(err);
      res.send(500, err);
    });
    readstream.on("error", function(err) {
      console.error(err);
      res.send(500, err);
    });
    console.log("Success");
    readstream.pipe(res);
  });

router
  .route("/download_by_hash/:hash")

  // Get a file for download
  .get(function(req, res) {
    console.log("download_by_hash", req.params.hash);

    var gridfs = Grid(mongoose.ctrl_conn.db);

    gridfs.files.findOne({ "metadata.hash": req.params.hash }, function(
      err,
      file
    ) {
      console.log(file);
      var readstream = gridfs.createReadStream({
        _id: file._id
      });
      req.on("error", function(err) {
        console.error(err);
        res.send(500, err);
      });
      readstream.on("error", function(err) {
        console.error(err);
        res.send(500, err);
      });
      console.log("Success");
      readstream.pipe(res);
    });
  });

// Working on getting PDBs from PDBQuery results
router
  .route("/get_pdb_by_hash/:hash")

  .get(function(req, res) {
    console.log("get_pdb_by_hash", req.params.hash);

    // HACK
    res.download("P41212.1.pdb");

  //   /*
  //   // Get the tar file out of the database
  //   var gridfs = Grid(mongoose.ctrl_conn.db);

  //   gridfs.files.findOne({ "metadata.hash": req.params.hash }, function(
  //     err,
  //     file
  //   ) {

  //     console.log("Retrieved:")
  //     console.log(file);

  //     if (file === null) {
  //       res.send(500, "Error finding file");
  //       return false;
  //     }

  //     var readstream = gridfs.createReadStream({
  //       _id: file._id
  //     });
  //     req.on("error", function(err) {
  //       console.error(err);
  //       res.send(500, err);
  //     });

  //     readstream.on("error", function(err) {
  //       console.error(err);
  //       res.send(500, err);
  //     });

  //     console.log(readstream);

  //     class MyWritable extends stream.Writable {
  //       _write(chunk, encoding, callback) {
  //         console.log(chunk);
  //         // if (chunk.toString().indexOf('a') >= 0) {
  //         //   callback(new Error('chunk is invalid'));
  //         // } else {
  //         //   callback();
  //         // }
  //         callback();
  //       }
  //     }

  //     let xform = new MyWritable;
  //     // xform.on("data", function(data) {
  //     //   console.log(data);
  //     // })
      
  //     readstream.pipe(xform);


  //     // // Convert base64 string to byte array
  //     // var converter = new stream.Writable();
  //     // converter.data = []; // We'll store all the data inside this array
  //     // converter._write = function(chunk) {
  //     //   this.data.push(chunk);
  //     // };
  //     // converter.on("end", function() {
  //     //   // Will be emitted when the input stream has ended, ie. no more data will be provided
  //     //   var b = Buffer.concat(this.data); // Create a buffer from all the received chunks
  //     //   // Insert your business logic here
  //     //   console.log(b);
  //     // });
  //     // readstream.pipe(converter);

      
  //     // streamToBuffer(readstream, function (err, buffer) {
  //     //   console.log(err);
  //     //   console.log(buffer);
  //     // });

  //     // var converter = new stream.Writable();
  //     // toString(converter, function (err, msg) {
  //     //   console.log(msg)
  //     // });
  //     // readstream.pipe(converter);
  //     // var byteCharacters = atob(res);
  //     // var byteNumbers = new Array(byteCharacters.length);
  //     // for (var i = 0; i < byteCharacters.length; i++) {
  //     //   byteNumbers[i] = byteCharacters.charCodeAt(i);
  //     // }
  //     // var byteArray = new Uint8Array(byteNumbers);

  //     // // Write to temporary file
  //     // var myFile = fs.createWriteStream("tmp.tar.bz2");
  //     // readstream.pipe(myFile);

     
  //   });
  
  });

// Temporary - will change to one of the above
router
  .route("/download_pdb/:file")

  // Get a file for download
  .get(function(req, res) {
    console.log("download_pdb", req.params.file);

    // res.download("1qrv.pdb");
    res.download("P41212.1.pdb");

    // var gridfs = Grid(mongoose.ctrl_conn.db);

    // gridfs.files.findOne({ 'metadata.hash': req.params.hash}, function (err, file) {
    //   console.log(file);
    //   var readstream = gridfs.createReadStream({
    //     _id: file._id
    //   });
    //   req.on("error", function(err) {
    //     console.error(err);
    //     res.send(500, err);
    //   });
    //   readstream.on("error", function(err) {
    //     console.error(err);
    //     res.send(500, err);
    //   });
    //   console.log("Success");
    //   readstream.pipe(res);
    // });
  });

router
  .route("/download_map/:file")

  // Get a file for download
  .get(function(req, res) {
    console.log("download_pdb", req.params.file);

    // res.download("1qrv.pdb");
    res.download("P41212_all_0_adf.map");

    // var gridfs = Grid(mongoose.ctrl_conn.db);

    // gridfs.files.findOne({ 'metadata.hash': req.params.hash}, function (err, file) {
    //   console.log(file);
    //   var readstream = gridfs.createReadStream({
    //     _id: file._id
    //   });
    //   req.on("error", function(err) {
    //     console.error(err);
    //     res.send(500, err);
    //   });
    //   readstream.on("error", function(err) {
    //     console.error(err);
    //     res.send(500, err);
    //   });
    //   console.log("Success");
    //   readstream.pipe(res);
    // });
  });

module.exports = router;
