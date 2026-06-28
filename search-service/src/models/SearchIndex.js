const { DataTypes } = require('sequelize');
const sequelize = require('../config/db');

const SearchIndex = sequelize.define('SearchIndex', {
    postId: { type: DataTypes.INTEGER, primaryKey: true },
    title: { type: DataTypes.STRING, allowNull: false },
    description: { type: DataTypes.TEXT },
    price: { type: DataTypes.DECIMAL(10, 2) },
    categoryId: { type: DataTypes.INTEGER },
    imageUrl: { type: DataTypes.STRING },
    categoryName: { type: DataTypes.STRING },
    status: { type: DataTypes.STRING }
});

module.exports = SearchIndex;