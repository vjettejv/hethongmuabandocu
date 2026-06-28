const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { Sequelize } = require('sequelize');
const AuthUser = require('../models/AuthUser');

const loginHandler = async ({ username, email, password }) => {
    const loginIdentifier = username || email;
    
    const user = await AuthUser.findOne({ 
        where: {
            [Sequelize.Op.or]: [
                { email: loginIdentifier },
                { username: loginIdentifier }
            ]
        }
    });

    if (!user || !(await bcrypt.compare(password, user.password))) {
        throw new Error('Invalid credentials');
    }
    return user;
};

module.exports = loginHandler;