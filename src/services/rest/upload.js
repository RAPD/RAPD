/*eslint-disable*/
var express = require("express");
var multer = require("multer");
var fs = require("fs");
var app = express();

var DIR = "./uploads/";

var upload = multer({ dest: DIR });

// app.use(function (req, res, next) {
//   res.setHeader('Access-Control-Allow-Origin', 'http://localhost:4200');
//   res.setHeader('Access-Control-Allow-Methods', 'POST');
//   res.setHeader('Access-Control-Allow-Headers', 'X-Requested-With,content-type');
//   res.setHeader('Access-Control-Allow-Credentials', true);
//   next();
// });

//create a cors middleware
app.use(function(req, res, next) {
  //set headers to allow cross origin request.
  res.header("Access-Control-Allow-Origin", "*");
  res.header("Access-Control-Allow-Methods", "PUT, GET, POST, DELETE, OPTIONS");
  res.header(
    "Access-Control-Allow-Headers",
    "Origin, X-Requested-With, Content-Type, Accept"
  );
  next();
});

app.get("/api", function(req, res) {
  res.end("file catcher example");
});

app.post("/api", function(req, res) {
  console.log("/api");
  var path = "";
  upload(req, res, function(err) {
    if (err) {
      // An error occurred when uploading
      console.log(err);
      return res.status(422).send("an Error occured");
    }
    // No error occured.
    path = req.file.path;
    return res.send("Upload Completed for " + path);
  });
});

var PORT = process.env.PORT || 3003;

app.listen(PORT, function() {
  console.log("Working on port " + PORT);
});
