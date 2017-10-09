var express = require('express');
var router =  express.Router();

const Image = require('../models/image');

// route to return image data given an id (GET api/images/:image_id)
router.route('/images/:image_id')
  .get(function(req, res) {
    Image.
      findOne({_id:req.params.image_id}).
      exec(function(err, image) {
        if (err) {
          console.error(err);
          res.send(err);
        } else {
          console.log('Image retrieved', image);
          res.json(image);
        }
      });
  });

module.exports = router;
