var mongoose = require('mongoose');
var Schema = mongoose.Schema;
// var bcrypt = require('bcryptjs');
var LoginSchema = new Schema({
  browser: {
    type: String,
    required: true
  },
  email: {
    type: String,
    required: true
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
  browser_version: {
    type: String,
    required: true
  },
}, {strict:false})

module.exports = mongoose.model('Login', LoginSchema);
