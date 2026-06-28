const checkFavoriteHandler = require('../queries/checkFavoriteHandler');
const getMyFavoritesHandler = require('../queries/getMyFavoritesHandler');

const checkFavorite = async (req, res) => {
    try {
        const result = await checkFavoriteHandler(req.user.id, req.params.postId);
        res.json(result);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};

const getMyFavorites = async (req, res) => {
    try {
        const result = await getMyFavoritesHandler(req.user.id);
        res.json(result);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};

module.exports = { checkFavorite, getMyFavorites };