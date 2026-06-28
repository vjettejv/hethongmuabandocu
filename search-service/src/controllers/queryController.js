const searchHandler = require('../queries/searchHandler');

const search = async (req, res) => {
    try {
        const results = await searchHandler(req.query);
        res.json(results);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};

module.exports = { search };