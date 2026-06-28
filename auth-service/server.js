const express = require('express');
const cors = require('cors');
require('dotenv').config();

const sequelize = require('./src/config/db');
const routes = require('./src/routes');

const app = express();
app.use(express.json());
app.use(cors());

// Sync DB
sequelize.sync({ alter: true })
    .then(() => console.log('Auth DB synced'))
    .catch(err => console.error('DB Sync Error:', err));

// Routes
app.use('/', routes);

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => console.log(`Auth Service running on port ${PORT}`));
