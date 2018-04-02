var mongoose = require('mongoose');
var Schema = mongoose.Schema;

var ProjectSchema = new Schema({
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
  description: {
    type: String,
    required: false
  },
  group: {
    type: Schema.Types.ObjectId,
    ref: 'Group',
    required: true,
  },
  last_action: {
    type: Schema.Types.ObjectId,
    ref: 'Result',
    reuired: false
  },
  last_timestamp: {
    type: Date,
    required: true,
    default: Date.now
  },
  project_type: {
    type: String,
    required: true,
    default: 'mx'
  },
  results: {
    type: [Schema.Types.ObjectId],
    default: [],
    ref: 'Result'
  },
  source_data: {
    type: [Schema.Types.ObjectId],
    ref: 'Result',
    default: []
  },
  title: {
    type: String,
    required: true,
    default: 'None'
  },
}, {strict:false});

module.exports = mongoose.model('Project', ProjectSchema);
