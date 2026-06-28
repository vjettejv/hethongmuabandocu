const express = require('express');
const cors = require('cors');
require('dotenv').config();

const sequelize = require('./src/config/db');
const Category = require('./src/models/Category');
const routes = require('./src/routes');

const app = express();
app.use(express.json());
app.use(cors());

sequelize.sync().then(() => {
    console.log('Category DB synced');
    Category.count().then(count => {
        if (count === 0) {
            Category.bulkCreate([
                { name: 'Electronics', description: 'Phones, Laptops, etc.' },
                { name: 'Furniture', description: 'Tables, Chairs, etc.' },
                { name: 'Clothing', description: 'Shirts, Pants, etc.' }
            ]);
        }
    });
});

app.use('/', routes);

const PORT = process.env.PORT || 3004;
app.listen(PORT, () => console.log(`Category Service running on port ${PORT}`));