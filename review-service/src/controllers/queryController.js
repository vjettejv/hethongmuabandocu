const getReviewsHandler = require('../queries/getReviewsHandler');

const getReviews = async (req, res) => {
    try {
        const reviews = await getReviewsHandler(req.params.userId, req.query);
        res.json(reviews);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};

module.exports = { getReviews };