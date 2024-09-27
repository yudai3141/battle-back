const router = require("express").Router();
const Notification = require("../models/Notification");
const User = require('../models/User');

// 通知を作成する
router.post('/', async (req, res) => {
    try {
      const newNotification = new Notification(req.body);
      const savedNotification = await newNotification.save();
      res.status(200).json(savedNotification);
    } catch (err) {
      console.error(err); // エラーをコンソールに出力
      res.status(500).json(err);
    }
  });

// ユーザーの通知を取得する
router.get('/:userId', async (req, res) => {
    try {
      const notifications = await Notification.find({ receiverId: req.params.userId });
  
      // senderUsernameを取得
      const notificationsWithUsernames = await Promise.all(
        notifications.map(async (notification) => {
          const sender = await User.findById(notification.senderId);
          return {
            ...notification._doc,
            senderUsername: sender.username,
          };
        })
      );
  
      res.status(200).json(notificationsWithUsernames);
    } catch (err) {
      console.error(err); // エラーをコンソールに出力
      res.status(500).json({ error: 'サーバーエラーが発生しました' });
    }
  });

// 通知を既読に更新する
router.put('/:id/read', async (req, res) => {
    try {
      await Notification.findByIdAndUpdate(req.params.id, {
        isRead: true,
      });
      res.status(200).json('Notification marked as read');
    } catch (err) {
      console.error(err);
      res.status(500).json(err);
    }
  });
  

module.exports = router;