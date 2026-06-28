const createReviewHandler = require('../commands/createReviewHandler');
const updateReviewHandler = require('../commands/updateReviewHandler');
const deleteReviewHandler = require('../commands/deleteReviewHandler');

const createReview = async (req, res) => {
    try {
        const review = await createReviewHandler(req.body, req.file);
        res.status(201).json(review);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};

const updateReview = async (req, res) => {
    try {
        const review = await updateReviewHandler(req.params.id, req.body, req.file);
        res.json(review);
    } catch (error) {
        if (error.message === 'Review not found') return res.status(404).json({ error: error.message });
        res.status(500).json({ error: error.message });
    }
};

const deleteReview = async (req, res) => {
    try {
        const result = await deleteReviewHandler(req.params.id);
        res.json(result);
    } catch (error) {
        if (error.message === 'Review not found') return res.status(404).json({ error: error.message });
        res.status(500).json({ error: error.message });
    }
};

module.exports = { createReview, updateReview, deleteReview };