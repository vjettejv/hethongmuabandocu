const { DataTypes } = require('sequelize');
const sequelize = require('../config/db');

const AuthUser = sequelize.define('AuthUser', {
    username: { type: DataTypes.STRING },
    email: { type: DataTypes.STRING }
});

module.exports = AuthUser;