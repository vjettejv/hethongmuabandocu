const Favorite = require('../models/Favorite');

const toggleFavoriteHandler = async (userId, postId) => {
    const existing = await Favorite.findOne({ where: { userId, postId } });
    if (existing) {
        await existing.destroy();
        return { message: 'Removed from favorites', isFavorited: false };
    } else {
        await Favorite.create({ userId, postId });
        return { message: 'Added to favorites', isFavorited: true };
    }
};

module.exports = toggleFavoriteHandler;