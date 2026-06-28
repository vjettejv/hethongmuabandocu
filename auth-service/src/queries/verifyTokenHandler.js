const jwt = require('jsonwebtoken');

const verifyTokenHandler = async (token) => {
    if (!token) throw new Error('No token provided');

    return new Promise((resolve, reject) => {
        jwt.verify(token, process.env.JWT_SECRET || 'supersecret', (err, decoded) => {
            if (err) reject(new Error('Invalid token'));
            resolve({ valid: true, user: decoded });
        });
    });
};

module.exports = verifyTokenHandler;
