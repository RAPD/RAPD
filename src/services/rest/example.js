const express = require('express')
const app = express()

var mongoose = require('mongoose');
var Grid = require('gridfs-stream');
Grid.mongo = mongoose.mongo;
var conn = mongoose.connect('mongodb://127.0.0.1:27017/example', {
  useMongoClient: true,
  useNewUrlParser: true
}, function(error) {
  console.error(error);
});
var gridfs;
conn.once('open', function () {
  gridfs = Grid(conn.db);
});

app.get('/download_by_id/:id', function(req, res) {
  console.log('download_by_id', req.params.id);

  var readstream = gridfs.createReadStream({
    _id: req.params.id
  });
  req.on('error', function(err) {
    console.error(err);
    res.send(500, err);
  });
  readstream.on('error', function (err) {
    console.error(err);
    res.send(500, err);
  });
  console.log('Success');
  readstream.pipe(res);

});

app.listen(3001, () => console.log('Example app listening on port 3000!'))
