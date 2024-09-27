const mongoose = require("mongoose");

const PostSchema = new mongoose.Schema({

        userId: {
            type: String,
            require: true,
        },

        desc: { 
            type: String
        },
        img: {
            type: String,
        },
        likes: {
            type: Array,
            default: [],
        },
        parentPostId: {
            type: String,
            default: null,
        },
        childPostIds: {  
            type: [String],
            default: [],
        },
        battleRequested: {
            type: Boolean,
            default: false,
        },
    },
    {timestamps: true}
);

module.exports = mongoose.model("POST",PostSchema);