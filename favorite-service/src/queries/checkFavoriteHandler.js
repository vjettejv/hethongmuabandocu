const Favorite = require('../models/Favorite');

const checkFavoriteHandler = async (userId, postId) => {
    const favorite = await Favorite.findOne({ where: { userId, postId } });
    return { isFavorited: !!favorite };
};

module.exports = checkFavoriteHandler;