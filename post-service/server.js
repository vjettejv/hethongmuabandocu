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

sequelize.sync().then(() => console.log('Post DB synced'));

app.use('/', routes);

app.use((err, req, res, next) => {
    console.error("Unhandled error:", err);
    res.status(500).json({ error: 'Internal Server Error', details: err.message });
});

const PORT = process.env.PORT || 3003;
app.listen(PORT, () => console.log(`Post Service running on port ${PORT}`));