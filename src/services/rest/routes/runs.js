var express = require('express');
var router = express.Router();
var mongoose = require('../models/mongoose');

// MongoDB model
const Run = mongoose.ctrl_conn.model('Run', require('../models/run').RunSchema);

// Routes that end with runs
// -----------------------------------------------------------------------------
// route to return image data given an id (GET api/runs/:run_id)
router.route('/runs/:run_id')
  .get(function(req, res) {

    Run.
      findOne({_id:req.params.run_id}).
      exec(function(err, run) {
        if (err) {
          console.error(err);
          res.status(500).json({
            success: false,
            message: err
          });
        } else {
          console.log('Returning run', run);
          res.status(200).json({
            success: true,
            run: run
          });
        }
      });
  });

module.exports = router;
