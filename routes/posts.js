const router = require("express").Router();
const Post = require("../models/Post");
const User = require("../models/User");

// 投稿を作成する
router.post("/", async (req,res) => {
    const newPost = new Post(req.body);
    try {
        const savedPost = await newPost.save();
        return res.status(200).json(savedPost);
    } catch(e) {
        return res.status(500).json(e);
    }
})

// 投稿を更新する
router.put("/:id", async(req, res)=> {
    try {
        const post = await Post.findById(req.params.id);
        if (post.userId === req.body.userId) {
            await post.updateOne({
                $set: req.body,
            })
            return res.status(200).json("投稿編集に成功しました！")
        }
        else {
            return res.status(403).json("他のユーザーの投稿は編集できません。")
        }
    } catch(e) {
        return res.status(500).json(e)
    }
})

// 投稿を削除する
router.delete("/:id", async(req, res)=> {
    try {
        const post = await Post.findById(req.params.id);
        if (post.userId === req.body.userId) {
            await post.deleteOne();
            return res.status(200).json("投稿削除に成功しました！")
        }
        else {
            return res.status(403).json("他のユーザーの投稿は削除できません。")
        }
    } catch(e) {
        return res.status(500).json(e)
    }
})


// 投稿を取得する
router.get("/:id", async(req, res)=> {
    try {
        const post = await Post.findById(req.params.id);
        return res.status(200).json(post);
    } catch(e) {
        return res.status(500).json(e)
    }
})

//特定の投稿にいいねを押す
router.put("/:id/like", async(req, res) => {
    try {
        const post = await Post.findById(req.params.id);
        // まだ投稿にいいねが押されていなければ押せる   
        if (!post.likes.includes(req.body.userId)) {
            await post.updateOne({
                $push: {
                    likes: req.body.userId
                }
            });
            return res.status(200).json("いいねを押しました！");
        } else {
            // いいねしているユーザIDを取り除く
            await post.updateOne({
                $pull: {
                    likes: req.body.userId
                }
            });
            return res.status(200).json("いいねを外しました。");
        }
    } catch(e) {
        return res.status(500).json(e);
    }
})

// プロフィール専用のタイムラインの取得
router.get("/profile/:username", async(req,res) => {
    try {
        const user = await User.findOne({username: req.params.username});
        const posts = await Post.find({userId: user._id});
        
        return res.status(200).json(posts);
    } catch(e) {
        res.status(500).json(e);
    }
})

// タイムラインの投稿を取得する
router.get("/timeline/:userId", async(req,res) => {
    try {
        const currentUser = await User.findById(req.params.userId);
        const userPosts = await Post.find({userId: currentUser._id});
        // 自分がフォローしているユーザーの投稿を全て取得
        const friendPosts = await Promise.all(
            currentUser.followings.map((friendId) => {
                return Post.find({userId: friendId});
            })
        );
        return res.status(200).json(userPosts.concat(...friendPosts));
    } catch(e) {
        res.status(500).json(e);
    }
})

module.exports = router;
