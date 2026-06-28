const express = require('express');
const cors = require('cors');
require('dotenv').config();

const routes = require('./src/routes');

const app = express();
app.use(express.json());
app.use(cors());

app.use('/', routes);

const PORT = process.env.PORT || 3004;
app.listen(PORT, () => console.log(Category Service running on port \));