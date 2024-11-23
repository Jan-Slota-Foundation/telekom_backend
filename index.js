const express = require("express");
var cors = require("cors");
const app = express();
const csv = require("csv-parser");
const fs = require("fs");
const results = [];
let frontendResults = [];

app.use(cors());

const PORT = process.env.PORT || 3000;

const readCSVFile = () => {
    return new Promise((resolve, reject) => {
        fs.createReadStream('./juice-shop_vulnerabilities_2024-11-14T1526.csv')
            .on('error', (error) => {
                console.error('Error reading file:', error);
                reject(error);
            })
            .pipe(csv())
            .on('data', (data) => results.push(data))
            .on('end', () => {
                frontendResults = results.map(row => ({
                    Vulnerability: row.Vulnerability,
                    Severity: row.Severity,
                    Details: row.Details
                }));
                resolve(frontendResults);
            })
            .on('error', (error) => {
                console.error('Error parsing CSV:', error);
                reject(error);
            });
    });
};

app.get("/vulnerabilities", (req, res) => {
    res.json(frontendResults);
});

app.get("/", (req, res) => {
    res.status(200);
    res.send("Hello, World!");
});

app.get("/test", (req, res) => {
    res.set('Cache-Control', 'no-store, no-cache, must-revalidate, private')
    res.status(200);
    res.send("test test");
});



//csv, str
app.post("/analyze",(res, req) =>{
    
    const data = req.body;
    console.log(data);
    res.send("Data sent succesfully");
});

// Using async/await to wait for CSV processing
async function initializeServer() {
    try {
        const data = await readCSVFile();
        console.log('Complete filtered results:', data);
        
        app.listen(PORT, () => {
            console.log(`Server running on port ${PORT}`);
        });
    } catch (error) {
        console.error('Error initializing server:', error);
    }
}

initializeServer();