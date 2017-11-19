var mongoose = require('mongoose');
var Schema = mongoose.Schema;
// var bcrypt = require('bcryptjs');
var ActivitySchema = new Schema({
  activity_type: {
    type: String,
    required: true
  },
  activity_subtype: {
    type: String,
    required: false
  },
  timestamp: {
    type: Date,
    default: Date.now
  },
  user: {
    type: Schema.Types.ObjectId,
    ref: 'User',
    required: false,
  }
}, {strict:false})

module.exports = mongoose.model('Activity', ActivitySchema);
