var mongoose = require('mongoose');
var Schema = mongoose.Schema;

var SessionSchema = new Schema({
  start: {
    type: Date
  },
  end: {
    type: Date
  },
  data_root_directory: {
    type: String,
    default: ''
  },
  site: {
    type: String,
    required: true
  },
  session_type: {
    type: String,
    required: true,
    default: 'mx'
  },
  user: {
    type: String,
    required: true,
  },
  timestamp: {
    type: Date,
    default: Date.now
  }
}, {strict:false});

module.exports = mongoose.model('Session', SessionSchema);
