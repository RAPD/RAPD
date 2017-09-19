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
  timestamp: {
    type: Date,
    default: Date.now
  }
}, {strict:false});

module.exports = mongoose.model('Project', ProjectSchema);
