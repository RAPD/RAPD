var mongoose = require('mongoose');
var Schema = mongoose.Schema;

var ResultSchema   = new Schema({}, {strict:false});

var ResultSchema = new Schema({
   _id: {
     type: Schema.ObjectId,
     auto: true
  },
  display: {
    type: String,
    required: false
  },
  plugin_id: {
    type: String,
    required: true
  },
  plugin_type: {
    type: String,
    required: true
  },
  plugin_version: {
    type: String,
    required: true
  },
  projects: {
    type: [Schema.Types.ObjectId],
    required: false,
    default: [],
    ref: 'Project'
  },
  repr: {
    type: String,
    required: true
  },
  result_id: {
    type: Schema.Types.ObjectId,
    required: true,
  },
  result_type: {
    type: String,
    required: true
  },
  session_id: {
    type: Schema.Types.ObjectId,
    ref: 'Session',
    required: true,
  },
  status: {
    type: Number,
    required: true,
    default: 1
  },
  timestamp: {
    type: Date,
    default: Date.now
  }
}, {strict:false});

module.exports = mongoose.model('Results', ResultSchema);
