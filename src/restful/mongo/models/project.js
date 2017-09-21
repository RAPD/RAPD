var mongoose = require('mongoose');
var Schema = mongoose.Schema;

var ProjectSchema = new Schema({
  project_type: {
    type: String,
    required: true,
    default: 'mx'
  },
  group: {
    type: Schema.Types.ObjectId,
    ref: 'Group',
    required: true,
  },
  title: {
    type: String,
    required: true,
    default: 'None'
  },
  description: {
    type: String,
    required: false
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
}, {strict:false});

module.exports = mongoose.model('Project', ProjectSchema);
