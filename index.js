const express = require("express");
var cors = require("cors");
const app = express();



app.use(cors()); // ak das toto prec bude incident

const PORT = process.env.PORT || 3000;


app.get("/", (req, res) => {
    res.status(200);
    res.send("Hello, World!");
})

app.get("/test", (req, res) => {
    // Disable caching
    res.set('Cache-Control', 'no-store, no-cache, must-revalidate, private')
    res.status(200);
    res.send("test test");
})

app.listen(PORT, ()=>{
    console.log(`Server runnuje ${PORT}`);
})

