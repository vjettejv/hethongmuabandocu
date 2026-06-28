const syncIndexHandler = require('../commands/syncIndexHandler');

const syncIndex = async (req, res) => {
    try {
        const result = await syncIndexHandler(req.body);
        res.status(200).json(result);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};

module.exports = { syncIndex };