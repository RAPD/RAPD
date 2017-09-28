var mongoose = require('mongoose');
var Schema = mongoose.Schema;

var GroupSchema = new Schema({
  creator: {
    type: Schema.Types.ObjectId,
    ref: 'User',
    required: true,
  },
  created: {
    type: Date,
    required: true,
    default: Date.now
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
