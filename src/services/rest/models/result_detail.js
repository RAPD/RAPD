var mongoose = require('mongoose');
var Schema = mongoose.Schema;
// var bcrypt = require('bcryptjs');

var ResultDetailSchema = new Schema({}, {strict:false})

module.exports = mongoose.model('ResultDetail', ResultDetailSchema);