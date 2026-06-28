const express = require('express');
const cors = require('cors');
require('dotenv').config();

const sequelize = require('./src/config/db');
const routes = require('./src/routes');

const app = express();
app.use(express.json());
app.use(cors());

sequelize.sync({ alter: true }).then(() => console.log('Search DB synced'));

app.use('/', routes);

const PORT = process.env.PORT || 3008;
app.listen(PORT, () => console.log(`Search Service running on port ${PORT}`));