var mongoose = require('mongoose');
var Schema = mongoose.Schema;
// var bcrypt = require('bcryptjs');

var RunSchema = new Schema({}, {strict:false})

// module.exports = mongoose.model('Run', RunSchema);
exports.Run = mongoose.model('Run', RunSchema);
exports.RunSchema = RunSchema;
