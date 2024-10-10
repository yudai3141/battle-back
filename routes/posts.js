const router = require("express").Router();
const Post = require("../models/Post");
const User = require("../models/User");

// // 全ての投稿を取得する
// router.get('/', async (req, res) => {
//     try {
//       const posts = await Post.find().populate('userId', 'username');
//       res.status(200).json(posts);
//     } catch (err) {
//       res.status(500).json(err);
//     }
//   });
  

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
        const post = await Post.findById(req.params.id).populate('userId', 'username _id');
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
        const posts = await Post.find({userId: user._id, parentPostId: null});
        return res.status(200).json(posts);
    } catch(e) {
        res.status(500).json(e);
    }
})

router.get("/timeline/:userId", async (req, res) => {
    try {
            // const currentUser = await User.findById(req.params.userId);
            // const userPosts = await Post.find({ userId: currentUser._id, parentPostId: null })
            // const friendPosts = await Promise.all(
            //     currentUser.followings.map((friendId) => {
            //         return Post.find({ userId: friendId, parentPostId: null })
            //     })
            // );
            // return res.status(200).json(userPosts.concat(...friendPosts));
        const allPosts = await Post.find({ parentPostId: null });

        return res.status(200).json(allPosts);
    } catch (e) {
        res.status(500).json(e);
    }
});




// 返信を作成する
router.post("/:id/reply", async (req, res) => {
    try {
        // 新しい返信投稿を作成
        const newReply = new Post({
            userId: req.body.userId,
            desc: req.body.desc,
            img: req.body.img,
            parentPostId: req.params.id,
        });

        // 返信を保存
        const savedReply = await newReply.save();

        // 親投稿のchildPostIdsに返信のIDを追加
        await Post.findByIdAndUpdate(req.params.id, {
            $push: { childPostIds: savedReply._id },
        });

        return res.status(200).json(savedReply);
    } catch (e) {
        return res.status(500).json(e);
    }
});

// 特定の投稿とその返信を取得する
router.get("/:id/thread", async (req, res) => {
    try {
        const getPostWithReplies = async (postId) => {
            const post = await Post.findById(postId);
            const replies = await Promise.all(
                post.childPostIds.map(async (childId) => {
                    return await getPostWithReplies(childId);
                })
            );
            return { post, replies };
        };

        const thread = await getPostWithReplies(req.params.id);
        return res.status(200).json(thread);
    } catch (e) {
        return res.status(500).json(e);
    }
});


// 特定の投稿とその子供の投稿を取得する
router.get("/:id/details", async (req, res) => {
    try {
        // 投稿を取得
        const post = await Post.findById(req.params.id);
        // 子供の投稿を取得
        const childPosts = await Post.find({ parentPostId: req.params.id });
        res.status(200).json({ post, childPosts });
    } catch (e) {
        res.status(500).json(e);
    }
});

module.exports = router;
