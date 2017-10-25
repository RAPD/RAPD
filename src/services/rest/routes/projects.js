var express = require('express');
var router = express.Router();
var mongoose = require('mongoose');

// MongoDB Models
var Project = require('../models/project');
var Result = require('../models/result');

// Routes that end with projects
// ----------------------------------------------------
router.route('/projects')
  // route to return all projects
  .get(function(req, res) {

    let query_params = {group:{$in:req.decoded._doc.groups}};
    if (req.decoded._doc.role == 'site_admin') {
      query_params = {};
    }

    Project.
      find(query_params).
      populate('group', 'groupname').
      exec(function(err, projects) {
        if (err) {
          console.error(err);
          res.status(500).json({
            success: false,
            message: err
          });
        } else {
          console.log('Returning', projects.length, 'projects');
          res.status(200).json({
            success: true,
            projects: projects
          });
        }
      });
  });

router.route('/projects/:project_id')
  // route to add or modify project
  .put(function(req, res) {

    let project = req.body.project;

    // Updating
    if (project._id) {
      Project.findByIdAndUpdate(user._id, user, {new:true})
      .populate('results')
      .exec(function(err, return_project) {
        if (err) {
          console.error(err);
          res.status(500).json({
            success: false,
            message: err
          });
        } else {
          console.log('Project edited successfully', return_project);
          res.status(200).json({
            success: true,
            user: return_project
          });
        }
      });

    // Creating
    } else {

      project.creator = req.decoded._doc._id;

      // Save the project
      Project.findOneAndUpdate(
        {_id:mongoose.Types.ObjectId()},
        project,
        {new:true, upsert:true}
      )
      exec(function(err, return_project) {
        if (err) {
          console.error(err);
          res.status(500).json({
            success:false,
            error:err
          });
        } else {
          console.log('Project created successfully', return_project);
          res.status(200).json({
            success: true,
            project: return_project
          });
        }
      });
    }
  });

// /projects/add_result
router.route('/projects/add_result')
  // route to add or modify project
  .put(function(req, res) {

    let project_id = req.body.project_id,
        result = req.body.result;

    // Make sure project._id is in results.projects for result._id
    Result.findOneAndUpdate({_id:result._id}, {$addToSet:{projects:project_id}})
    .exec(function(err1, return_result) {
      if (err1) {
        console.error(err1);
        res.json({
          success:false,
          error:err1
        });
      // 1st update was successful
      } else {
        // Now make sure the result is in the project.results
        Project.findOneAndUpdate({_id:project_id}, {$addToSet:{results:result._id}})
        .populate('results')
        .exec(function(err2, return_project) {
          if (err2) {
            console.error(err2);
            res.status(500).json({
              success:false,
              error:err2
            });
          } else {
            console.log('Result marked with project', return_result);
            console.log('Results added to project', return_project);
            res.status(200).json({
              success:true,
              result:return_result,
              project:return_project,
            });
          }
        });
      }
    });

  });

module.exports = router;
