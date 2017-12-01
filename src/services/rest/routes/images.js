const { exec } = require('child_process');
const config =   require('../config');
var express =    require('express');
const fs =       require('fs');
const uuidv1 =   require('uuid/v1');

const Image = require('../models/image');

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
            console.log('Have image '+fullname+'!');

            let // jpeg_file = params_image._id+'.jpeg',
                jpeg_file = config.image_directory+params_image._id+params_image.view_color+'.jpeg',
                command = '/programs/i386-mac/system/sbgrid_bin/adxv -sa -colors '+params_image.view_color+' -jpeg_scale 0.6 '+fullname+' '+jpeg_file;

            console.log(command);

            if (fs.existsSync(jpeg_file)) {
              fs.readFile(jpeg_file, function(err, data) {
                 var base64data = new Buffer(data).toString('base64');
                 res.status(200).json({
                   success:true,
                   image_data:base64data
                 })
              });
            } else {
              exec(command, (error, stdout, stderr) => {
                if (error) {
                  console.error(`exec error: ${error}`);
                  return;
                }
                console.log(`stdout: ${stdout}`);
                console.log(`stderr: ${stderr}`);
                fs.readFile(jpeg_file, function(err, data) {
                   var base64data = new Buffer(data).toString('base64');
                   res.status(200).json({
                     success:true,
                     image_data:base64data
                   })
                });
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
          }
        }
      });
  });

module.exports = router;
