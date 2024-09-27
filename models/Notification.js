const mongoose = require("mongoose");

const NotificationSchema = new mongoose.Schema({
    senderId: { type: String, required: true }, // 通知を送ったユーザーID
    receiverId: { type: String, required: true }, // 通知を受け取るユーザーID
    type: { type: String, required: true }, // 通知の種類（例：レスバトルリクエスト）
    postId: { type: String, required: false }, // 関連する投稿のID
    isRead: { type: Boolean, default: false }, // 通知が既読かどうか
    battleId: { type: String, default: null },
    createdAt: { type: Date, default: Date.now },
});

module.exports = mongoose.model("Notification", NotificationSchema);