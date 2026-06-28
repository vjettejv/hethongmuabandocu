const express = require('express');
const cors = require('cors');
require('dotenv').config();

const routes = require('./src/routes');

const app = express();
app.use(express.json());
app.use(cors());

app.use('/', routes);

const PORT = process.env.PORT || 3006;
app.listen(PORT, () => console.log(`Notification Service running on port ${PORT}`));