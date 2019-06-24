var express = require("express");
var router = express.Router();
var mongoose = require("../models/mongoose");
var Grid = require("gridfs-stream");

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

    gridfs.files.findOne({ 'metadata.hash': req.params.hash}, function (err, file) {
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
