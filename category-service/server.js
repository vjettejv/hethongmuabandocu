const express = require('express');
require('dotenv').config();

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3004;
app.listen(PORT, () => console.log(Category Service running on port \));