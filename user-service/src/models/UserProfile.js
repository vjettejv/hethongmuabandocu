const { DataTypes } = require('sequelize');
const sequelize = require('../config/db');

const UserProfile = sequelize.define('UserProfile', {
    id: { type: DataTypes.INTEGER, primaryKey: true, autoIncrement: true },
    authId: { type: DataTypes.INTEGER, allowNull: false, unique: true },
    fullName: { type: DataTypes.STRING },
    phone: { type: DataTypes.STRING },
    address: { type: DataTypes.STRING },
    avatar: { type: DataTypes.STRING }
});

module.exports = UserProfile;