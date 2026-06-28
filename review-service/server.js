const express = require('express');
const cors = require('cors');
const path = require('path');
require('dotenv').config();

const sequelize = require('./src/config/db');
const routes = require('./src/routes');

const app = express();
app.use(express.json());
app.use(cors());

// Serve static
app.use('/uploads', express.static(path.join(__dirname, 'uploads')));

sequelize.sync({ alter: true }).then(() => console.log('Review DB synced'));

app.use('/', routes);

const PORT = process.env.PORT || 3007;
app.listen(PORT, () => console.log(`Review Service running on port ${PORT}`));