var mongoose = require('mongoose');
var Schema = mongoose.Schema;

var GroupSchema = new Schema({
  groupname: {
    type: String,
    default: 'unknown'
  },
  institution: {
    type: String,
    default: 'unknown'
  },
  status: {
    type: String,
    required: true,
    default: 'active'
  },
  uid: {
    type: String,
    required: true,
    unique: true
  },
  uidNumber: {
    type: Number,
    required: true,
    unique: true
  },
  gidNumber: {
    type: Number,
    required: true
  },
  timestamp: {
    type: Date,
    default: Date.now
  }
}, {strict:false});

module.exports = mongoose.model('Group', GroupSchema);
