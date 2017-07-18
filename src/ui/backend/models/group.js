var mongoose = require('mongoose');
var Schema = mongoose.Schema;

var GroupSchema = new Schema({
  groupname: {
    type: String,
    required: true
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
    type: Number,
    required: false
  },
  gid: {
    type: Number,
    required: false
  },
  timestamp: {
    type: Date,
    default: Date.now
  }
}, {strict:false});

module.exports = mongoose.model('Group', GroupSchema);
