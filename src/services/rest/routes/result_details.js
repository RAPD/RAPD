var express = require('express');
var router = express.Router();
var mongoose = require('../models/mongoose');

const Activity     = mongoose.ctrl_conn.model('Activity', require('../models/activity').ActivitySchema);
const Image        = mongoose.ctrl_conn.model('Image', require('../models/image').ImageSchema);
const Result       = mongoose.ctrl_conn.model('Result', require('../models/result').ResultSchema);
const ResultDetail = mongoose.ctrl_conn.model('ResultDetail', require('../models/result_detail').ResultDetailSchema);
const Session      = mongoose.ctrl_conn.model('Session', require('../models/session').SessionSchema);

// on routes that end in /result_details
// ----------------------------------------------------
router.route('/result_details/:result_id')
      .get(function(req, res) {
        Result.findOne({_id:req.params.result_id}, function(err, result) {
          if (err) {
            console.error(err);
            res.status(500).json({
              success: false,
              message: err
            });
          } else {
            console.log('Have result:', result);

            
            // Create a mongoose model for the result
            let name = (result._doc.data_type + '_' + result._doc.plugin_type +'_result').toLocaleLowerCase();
            console.log('name', name);
            let collection_name = name.charAt(0).toUpperCase() + name.slice(1);
            var ResultModel;
            try {
              if (mongoose.ctrl_conn.model(collection_name)) {
                ResultModel = mongoose.ctrl_conn.model(collection_name);
              }
            } catch(e) {
              if (e.name === 'MissingSchemaError') {
                let schema = new mongoose.Schema({
                  _id: {
                    type: mongoose.Schema.ObjectId,
                    auto: true
                    },
                }, {strict:false});
                ResultModel = mongoose.ctrl_conn.model(collection_name, schema);
              }
            }

            // Now get the result
            ResultModel.
            findOne({'process.result_id':mongoose.Types.ObjectId(result._id)}).
            exec(function(err, detailed_result) {
              
              // Error
              if (err) {
                console.error(err);
                res.status(500).json({
                  success: false,
                  message: err
                });
              
              // No error
              } else {
                console.log(detailed_result);
                if (detailed_result) {
                  // console.log(Object.keys(detailed_result));
                  // console.log(detailed_result._doc);
                  // console.log(detailed_result._doc.process);

                  // Make sure there is a process
                  if ('process' in detailed_result._doc) {
                    // If there is an image1_id
                    if ('image1_id' in detailed_result._doc.process) {

                      // Manually populate
                      Image.
                      findOne({_id:detailed_result._doc.process.image1_id}).
                      exec(function(err, image1) {
                        if (err) {
                          console.error(err);
                          return false;
                        } else {
                          detailed_result._doc.image1 = image1;
                          return detailed_result;
                          // console.log('POPULATED image1');
                          // console.log(detailed_result);
                          // Now look for image2
                          // if ('image2_id' in detailed_result._doc.process) {

                          //   // Manually populate
                          //   Image.
                          //   findOne({_id:detailed_result._doc.process.image1_id}).
                          //   exec(function(err, image2) {
                          //     if (err) {
                          //       console.error(err);
                          //       return false;
                          //     } else {
                          //       detailed_result._doc.image1 = image2;
                          //       // console.log('POPULATED image2');
                          //       // console.log(detailed_result);
                          //       // Send back
                          //       res.status(200).json({
                          //           success: true,
                          //           results: detailed_result
                          //       });
                          //     }
                          //   });

                          // // No image2_id
                          // } else {
                          //   // Send back
                          //   res.status(200).json({
                          //       success: true,
                          //       results: detailed_result
                          //   });
                          // }
                        }
                      })
                      .then(function(detailed_result) {
                        if ('image2_id' in detailed_result._doc.process) {

                          // Manually populate
                          Image.
                          findOne({_id:detailed_result._doc.process.image1_id}).
                          exec(function(err, image2) {
                            if (err) {
                              console.error(err);
                              return false;
                            } else {
                              detailed_result._doc.image1 = image2;
                              // console.log('POPULATED image2');
                              // console.log(detailed_result);
                              // Send back
                              // res.status(200).json({
                              //     success: true,
                              //     results: detailed_result
                              // });
                              return detailed_result;
                            }
                          });

                        // No image2_id
                        } else {
                          // Send back
                          // res.status(200).json({
                          //     success: true,
                          //     results: detailed_result
                          // });
                          return detailed_result;
                        }
                      })
                      .then();

                    // No image1_id
                    } else {
                      // Send back
                      res.status(200).json({
                        success: true,
                        results: detailed_result
                      });
                    }

                  // No process  
                  } else {
                    // Send back
                    res.status(200).json({
                        success: true,
                        results: detailed_result
                      });
                  }
                } else {
                  res.status(200).json({
                    success: false,
                    message: "Unable to locate result detail"
                  });
                }
              }
            });
          }
        });
     });

module.exports = router;
