var mongoose = require('mongoose');
var Schema = mongoose.Schema;

var GroupSchema = new Schema({
  creator: {
    type: Schema.Types.ObjectId,
    ref: 'User',
    required: false,
  },
  created: {
    type: Date,
    required: true,
    default: Date.now
  },
  email: {
    type: String,
    required: false
  },
  gidNumber: {
    type: Number,
    required: true
  },
  groupname: {
    type: String,
    default: 'unknown'
  },
  institution: {
    type: String,
    default: 'unknown'
  },
  loginAttempts: {
    type: Number,
    required: false,
    default: 0
  },
  role: {
    type: String,
    required: false,
    default: 'user'
  },
  status: {
    type: String,
    required: true,
    default: 'active'
  },
  timestamp: {
    type: Date,
    default: Date.now
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
}, {strict:false});

module.exports = mongoose.model('Group', GroupSchema);
