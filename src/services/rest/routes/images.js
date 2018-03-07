const { exec } =     require('child_process');
const config =       require('../config');
var express =        require('express');
var findRemoveSync = require('find-remove')
const fs =           require('fs');
const mkdirp =       require('mkdirp');
const uuidv1 =       require('uuid/v1');
var mongoose = require('../models/mongoose');

const Image =  mongoose.ctrl_conn.model('Image', require('../models/image').ImageSchema);
// const Image = require('../models/image');

var router =  express.Router();

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

// route to return a jpeg of an imageid (GET api/image_jpeg/:image_id)
router.route('/image_jpeg/:image')
  .get(function(req, res) {

    console.log('/image_jpeg/:image', req.params.image);

    var params_image = req.params.image;
    if (!params_image) {
      next();
      return;
    }

    params_image = JSON.parse(req.params.image);

    // Get image data
    Image.
      findOne({_id:params_image._id}).
      exec(function(err, image_result) {

        if (err) {
          console.error(err);
          res.status(500).json({
            success: false,
            error: err
          });
        } else {

          let fullname = image_result._doc.fullname;
          // Make sure the image exists
          if (fs.existsSync(fullname)) {

            let jpeg_file = config.image_directory+params_image._id+params_image.view_color+'.jpg';

            // JPEG already exists
            if (fs.existsSync(jpeg_file)) {
              fs.readFile(jpeg_file, function(err, data) {
                 var base64data = new Buffer(data).toString('base64');
                 res.status(200).json({
                   success:true,
                   image_data:base64data
                 });
                 // Get rid of older files
                 var result = findRemoveSync(config.image_directory, {age: {seconds: 3600}, extensions: '.jpg'});
                 return true;
              });

            // Make the JPEG
            } else {

              // Make sure the directory exists
              mkdirp.sync(config.image_directory)
              // -jpeg_scale 0.6
              let command = config.adxv+' -sa -colors '+params_image.view_color+' '+fullname+' '+jpeg_file;
              console.log(command);

              exec(command, (error, stdout, stderr) => {
                if (error) {
                  console.error(`exec error: ${error}`);
                  res.status(500).json({
                    success: false,
                    error: err
                  });
                  return false;
                }

                console.log(`stdout: ${stdout}`);
                console.log(`stderr: ${stderr}`);

                // Read the file and send it
                if (fs.existsSync(jpeg_file)) {
                  fs.readFile(jpeg_file, function(err, data) {
                     var base64data = new Buffer(data).toString('base64');
                     res.status(200).json({
                       success:true,
                       image_data:base64data
                     });
                     // Get rid of older files
                     var result = findRemoveSync(config.image_directory, {age: {seconds: 3600}, extensions: '.jpg'});
                     return true;
                  });
                } else {
                  let err = 'JPEG file does not exist after creating it.'
                  console.error(err);
                  res.status(500).json({
                    success: false,
                    error: err
                  });
                  return false;
                }
              });
            }
          } else {
            // Return error
            let err = fullname+' does not exist'
            console.error(err);
            res.status(500).json({
              success: false,
              error: err
            });
            return false;
          }
        }
      });
  });

module.exports = router;
