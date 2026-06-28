const { DataTypes } = require('sequelize');
const sequelize = require('../config/db');

const AuthUser = sequelize.define('AuthUser', {
    username: { type: DataTypes.STRING, allowNull: false, unique: true },
    email: { type: DataTypes.STRING, allowNull: false, unique: true },
    password: { type: DataTypes.STRING, allowNull: false }
});

module.exports = AuthUser;