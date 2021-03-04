const config = require('../config');
var mongoose = require('mongoose');

// Fix the promise issue in Mongoose
mongoose.Promise = require('q').Promise;

// AUTHORIZATION CONNECTION
if (! config.auth_conn) {
  mongoose.auth_conn = ctrl_conn;
} else {
  console.log('Connecting to', config.auth_conn);
  mongoose.auth_conn = mongoose.createConnection(config.auth_conn, {
    // useMongoClient: true,
    useNewUrlParser: true
  }, function(error) {
    if (error) {
      console.error(error);
    }
  });
}

// CONTROL CONNECTION
console.log('Connecting to', config.control_conn);
mongoose.ctrl_conn = mongoose.createConnection(config.control_conn, {
  // useMongoClient: true,
  useNewUrlParser: true
}, function(error) {
  if (error) {
    console.error(error);
  }
});

module.exports = mongoose;
