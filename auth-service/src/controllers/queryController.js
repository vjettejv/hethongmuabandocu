const getUserByIdHandler = require('../queries/getUserByIdHandler');
const verifyTokenHandler = require('../queries/verifyTokenHandler');

const getUserById = async (req, res) => {
    try {
        const result = await getUserByIdHandler(req.params.id);
        res.json(result);
    } catch (error) {
        if (error.message === 'User not found') return res.status(404).json({ error: error.message });
        res.status(500).json({ error: error.message });
    }
};

const verifyToken = async (req, res) => {
    try {
        const token = req.headers.authorization?.split(' ')[1];
        const result = await verifyTokenHandler(token);
        res.json(result);
    } catch (error) {
        res.status(401).json({ error: error.message });
    }
};

module.exports = { getUserById, verifyToken };
