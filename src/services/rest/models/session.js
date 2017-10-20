var mongoose = require('mongoose');
var Schema = mongoose.Schema;

var SessionSchema = new Schema({
  data_root_directory: {
    type: String,
    default: ''
  },
  last_process: {
    type: Date,
    required: true,
    default: Date.now
  },
  group: {
    type: Schema.Types.ObjectId,
    ref: 'Group',
    required: true
  },
  session_type: {
    type: String,
    required: true,
    default: 'mx'
  },
  site: {
    type: String,
    required: true
  },
  timestamp: {
    type: Date,
    default: Date.now
  }
}, {strict:false});

module.exports = mongoose.model('Session', SessionSchema);
