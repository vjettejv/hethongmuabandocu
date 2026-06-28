const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { Sequelize } = require('sequelize');
const AuthUser = require('../models/AuthUser');

const loginHandler = async ({ username, email, password }) => {
    return null;
};

module.exports = loginHandler;