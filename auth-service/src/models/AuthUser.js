const { DataTypes } = require('sequelize');
const sequelize = require('../config/db');

const AuthUser = sequelize.define('AuthUser', {
    id: { type: DataTypes.INTEGER, primaryKey: true, autoIncrement: true },
    roleId: { type: DataTypes.INTEGER, defaultValue: 1 },
    username: { type: DataTypes.STRING, allowNull: false, unique: true },
    email: { type: DataTypes.STRING, allowNull: false, unique: true },
    password: { type: DataTypes.STRING, allowNull: false },
    isVerified: { type: DataTypes.BOOLEAN, defaultValue: false },
    otp: { type: DataTypes.STRING, allowNull: true }
}, { tableName: 'Users', timestamps: true });

module.exports = AuthUser;