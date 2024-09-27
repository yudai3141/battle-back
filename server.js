const express = require("express");
const app = express();
const userRoute = require("./routes/users");
const authRoute = require("./routes/auth");
const postRoute = require("./routes/posts");
const uploadRoute = require("./routes/upload");
const notificationRoute = require("./routes/notifications"); 
const battleRoute = require("./routes/battles"); 
const PORT = 5001; //何故か5000は使えなかった
const mongoose = require("mongoose");
const path = require("path");
const cors = require("cors");
require("dotenv").config();


app.use(express.json());
app.use(cors()); 

//DB接続
mongoose.connect(process.env.MONGOURL)
.then(() => {
    console.log("DBと接続中・・・");
}).catch((err) => {
    console.error("MongoDB接続エラー:", err.message);
});

// ミドルウェア
app.use("/images",express.static(path.join(__dirname, "public/images")));
app.use(express.json());
app.use("/api/users", userRoute);
app.use("/api/auth", authRoute);
app.use("/api/posts", postRoute);
app.use("/api/upload", uploadRoute);
app.use("/api/notifications", notificationRoute); 
app.use("/api/battles", battleRoute); 


app.get("/", (req,res) => {
    res.send("hello express");
});

// app.get("/users", (req,res) => {
//     res.send("users express");
// });


app.listen(PORT, () => console.log("サーバーが起動しました"));

