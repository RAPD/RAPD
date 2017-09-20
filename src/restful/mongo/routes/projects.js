var express = require('express');
var router = express.Router();

// MongoDB Models
var Project = require('../models/project');

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

module.exports = router;
