var mongoose = require('mongoose');
var Schema = mongoose.Schema;
// var bcrypt = require('bcryptjs');
var LoginSchema = new Schema({
  browser: {
    type: String,
    required: true
  },
  browser_version: {
    type: String,
    required: true
  },
  email: {
    type: String,
    required: false
  },
  ip_address: {
    type: String,
    required: true
  },
  os: {
    type: String,
    required: true
  },
  platform: {
    type: String,
    required: true
  },
  timestamp: {
    type: Date,
    default: Date.now
  },
  uid: {
    type: Number,
    required: false
  }
}, {strict:false})

module.exports = mongoose.model('Login', LoginSchema);
