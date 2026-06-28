const toggleFavoriteHandler = require('../commands/toggleFavoriteHandler');

const toggleFavorite = async (req, res) => {
    try {
        const result = await toggleFavoriteHandler(req.user.id, req.body.postId);
        res.status(result.isFavorited ? 201 : 200).json(result);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};

module.exports = { toggleFavorite };