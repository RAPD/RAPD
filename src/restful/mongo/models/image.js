var mongoose = require('mongoose');
var Schema = mongoose.Schema;
// var bcrypt = require('bcryptjs');

var ImageSchema = new Schema({}, {strict:false})

module.exports = mongoose.model('Image', ImageSchema);
