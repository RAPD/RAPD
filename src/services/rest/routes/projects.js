var express = require('express');
var router = express.Router();
var mongoose = require('../models/mongoose');

// MongoDB Models
const Project = mongoose.ctrl_conn.model('Project', require('../models/project').ProjectSchema);
const Result  = mongoose.ctrl_conn.model('Result', require('../models/result').ResultSchema);
const Session = mongoose.ctrl_conn.model('Session', require('../models/session').SessionSchema);

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
          console.log(projects);
          res.status(200).json({
            success: true,
            projects: projects
          });
        }
      });
  });

router.route('/projects/:project_id')
  // Get project data
  .get(function(req, res) {
    console.log(req.params.project_id)
    Project.findOne({_id:req.params.project_id}).
            populate({path:'source_data', model:"Result"}).
            // populate('results').
            exec(function(err, project) {
              if (err) {
                console.error(err);
                res.status(500).json({
                  success: false,
                  message: err
                });
              } else {

                console.log('Returning project', project);
                res.status(200).json({
                  success: true,
                  project: project
                });
              }
            });
  })

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
            operation: 'edit',
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
      .exec(function(err, return_project) {
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
            operation: 'create',
            project: return_project
          });
        }
      });
    }
  })

  // Delete the user with _id (DELETE api/projects/:project_id)
  .delete(function(req, res) {
    Project.remove({_id:req.params.project_id}, function(err) {
      if (err) {
        console.error(err);
        res.status(500).json({
          success: false,
          message: err
        });
      } else {
        console.log('Project deleted successfully', req.params.project_id);
        res.status(200).json({
          operation: 'delete',
          success: true,
          _id: req.params.project_id
        });
      }
    });
  });

// Add a result to a project
add_result = function(req, res) {

  console.log('add_result');

  let project_id = req.body.project_id,
      result = req.body.result;

  console.log(project_id);
  console.log(result);

  // Make sure result and project have same group?

  // Add result to project
  // MX data
  if (result.data_type === 'MX') {
    // source_data
    if (result.plugin_type in {INDEX:1, INTEGRATE:1}) {
      Project.findOneAndUpdate({_id:project_id}, {$addToSet:{source_data:result._id}}, {new:true})
      .exec(function(err, project2) {
        console.log(err, project2);
        if (err) {
          console.error(err);
          res.status(200).json({
            success:false,
            message:err
          });
        } else {
          console.log("Add source_data successful");
          res.status(200).json({
            success:true,
            message:'Successful'
          });
          // Add project to result
          Result.findOneAndUpdate({_id:result._id}, {$addToSet:{projects:project_id}});
        }
      })
    // results
    } else {
      Project.findOneAndUpdate({_id:project_id}, {$addToSet:{results:result._id}}, {new:true})
      .exec(function(err, project2) {
        console.log(err, project2);
        if (err) {
          console.error(err);
          res.status(200).json({
            success:false,
            message:err
          });
        } else {
          console.log("Add result successful");
          res.status(200).json({
            success:true,
            message:'Successful'
          });
          // Add project to result
          Result.findOneAndUpdate({_id:result._id}, {$addToSet:{projects:project_id}});
        }
      })
    }
  }
}

// /projects/add_result
router.route('/projects_add_result')
  // route to add or modify project
  .put(function(req, res) {

    let project_id = req.body.project_id,
        result = req.body.result;

    console.log(project_id);
    console.log(result);
    console.log(req.decoded._doc);
    
    // For testing
    // req.decoded._doc.role = 'foo';

    // Allowed to add to project?
    if (req.decoded._doc.role !== 'site_admin') {
      // User must have Session group_id
      let data_session_id = result.session_id;
      Session.findOne({_id:mongoose.Types.ObjectId(data_session_id)})
      .exec(function(err, session) {
        // console.log(err);
        // console.log(session);
        if (err) {
          console.error(err);
          res.status(200).json({
            success:false,
            message:err
          });
        // Have group_id
        } else {
          let group = req.decoded._doc.groups.find(o => o._id === session.group);
          // console.log(req.decoded._doc.groups);
          // console.log(session.group);
          // console.log(group);
          // No match - rejected
          if (group === undefined) {
            let error_message = 'User is not authorized to access this data';
            console.error(error_message);
            res.status(200).json({
              success:false,
              message:error_message
            });
            return false;
          // All is good
          } else {
            add_result(req, res);
          }
        }
      });
    // site_admin can do it!
    } else {
      add_result(req, res);
    }
  });

module.exports = router;
