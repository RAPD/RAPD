var express = require('express');
var router = express.Router();

// MongoDB model
var Run = require('../models/run');

// Routes that end with runs
// -----------------------------------------------------------------------------
// route to return image data given an id (GET http://localhost:8080/api/runs/:run_id)
router.route('/runs/:run_id')
  .get(function(req, res) {

    console.log('GET run:', req.params.run_id);

    Run.
      findOne({_id:req.params.run_id}).
      exec(function(err, run) {
        console.log(run);
        res.json(run);
      });
  });

module.exports = router;
