var express = require('express');
var router = express.Router();

// MongoDB Models
var Project = require('../models/project');
var Result = require('../models/result');

// Routes that end with projects
// ----------------------------------------------------
router.route('/projects')
  // route to return all projects
  .get(function(req, res) {
    console.log('GET /projects');
    console.log(req.decoded._doc);

    let find_search = { group: { $in: req.decoded._doc.groups}};
    if (req.decoded._doc.role == 'site_admin') {
      find_search = {};
    }

    Project.
      find(find_search).
      populate('group', 'groupname').
      exec(function(err, projects) {
        console.log(projects);
        res.json(projects);
      });
  })

  // route to add or modify project
  .put(function(req, res) {
    console.log('PUT /projects');

    let project = req.body.project;

    console.log(project);

    // Updating
    if (project._id) {
      res.json({
        success:false,
        error:'Project updating not currently supported'
      });
    // New
    } else {

      // Create a new project
      let new_project = new Project({
        project_type:project.project_type,
        title:project.title,
        description:project.description,
        group:project.group,
        creator:req.decoded._doc._id,
      });

      // Save the project
      new_project.save(function(err, return_project, numAffected) {
        if (err) {
          res.json({
            success:false,
            error:err
          });
        } else {
          console.log('Project saved successfully');
          res.json({
            success: true,
            operation: 'add',
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
    console.log('PUT /projects/add_result');

    let project_id = req.body.project_id,
        result = req.body.result;

    // console.log(project_id);
    console.log(result);

    // Make sure project._id is in results.projects for result._id
    Result.update({_id:result._id}, {$addToSet:{projects:project_id}}, function(err1, res1) {
      // console.log(err);
      // console.log(result);
      if (err1) {
        res.json({
          success:false,
          error:err1
        });
      // 1st update was successful
      } else {
        // Now make sure the result is in the project.results
        Project.update({_id:project_id}, {$addToSet:{results:result._id}}, function(err2, res2) {
          // console.log(err2);
          // console.log(res2);
          if (err2) {
            res.json({
              success:false,
              error:err2
            });
          } else {
            res.json({success:true});
          }
        });
      }
    });

  });

module.exports = router;
