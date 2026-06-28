const jwt = require('jsonwebtoken');

const verifyToken = (req, res, next) => {
    const token = req.headers.authorization?.split(' ')[1];
    if (!token) return res.status(401).json({ error: 'Unauthorized' });
    try {
        req.user = jwt.verify(token, 'supersecret');
    } catch(e) { res.status(401).json({ error: 'Invalid token' }); }
};

module.exports = verifyToken;