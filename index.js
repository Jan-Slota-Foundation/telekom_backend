const express = require("express");
var cors = require("cors");
const app = express();

app.use(cors());

const PORT = process.env.PORT || 3000;


app.get("/", (req, res) => {
    res.send("Hello, World!");
})

app.get("/test", (req, res) => {
    res.status(200);
    res.send("test test");
})

app.listen(PORT, ()=>{
    console.log(`Server runnuje ${PORT}`);
})

