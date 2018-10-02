var mongoose = require("mongoose");
var Schema = mongoose.Schema;

var UploadSchema = new Schema(
  {
    description: {
      type: String,
      required: false
    },
    hash: {
      type: String,
      required: true
    },
    // group: {
    //   type: Schema.Types.ObjectId,
    //   ref: "Group",
    //   required: true
    // },
    project_id: {
      type: Schema.Types.ObjectId,
      ref: "Project",
      required: false
    },
    // result_id: {
    //     type: Schema.Types.ObjectId,
    //     ref: "Result",
    //     required: false
    //   },
    status: {
      type: String,
      default: "shown"
    },
    timestamp: {
      type: Date,
      required: true,
      default: Date.now
    },
    user: {
      type: Schema.Types.ObjectId,
      ref: "User",
      required: true
    }
  },
  { strict: false }
);

module.exports = mongoose.model("Project", ProjectSchema);
