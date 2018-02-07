const config = require('../config');
var mongoose = require('mongoose');

// Fix the promise issue in Mongoose
mongoose.Promise = require('q').Promise;

// CONTROL CONNECTION
mongoose.ctrl_conn = mongoose.createConnection(config.control_conn, {
  useMongoClient: true,
}, function(error) {
  if (error) {
    console.error(error);
  }
});

// AUTHORIZATION CONNECTION
if (! config.auth_conn) {
  mongoose.auth_conn = ctrl_conn;
} else {
  console.log('Connecting to', config.auth_conn);
  mongoose.auth_conn = mongoose.createConnection(config.auth_conn, {
    useMongoClient: true,
  }, function(error) {
    if (error) {
      console.error(error);
    }
  });
}

// mongoose.main_conn = mongoose.createConnection('mongodb://localhost/main');
// mongoose.admin_conn = mongoose.createConnection('mongodb://localhost/admin');

module.exports = mongoose;
