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

  // get the session with that id (accessed at GET http://localhost:8080/api/bears/:bear_id)
  .get(function(req, res) {
    console.log("download_by_id", req.params.id);

    // console.log(mongoose.connection);
    var gridfs = Grid(mongoose.ctrl_conn.connection.db);

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

module.exports = router;
