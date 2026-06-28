const Favorite = require('../models/Favorite');

const getMyFavoritesHandler = async (userId) => {
    const favorites = await Favorite.findAll({ where: { userId } });
    if (favorites.length === 0) return [];

    const postPromises = favorites.map(f =>
        fetch((process.env.POST_SERVICE_URL || 'http://post-service:3003') + `/${f.postId}`)
            .then(r => r.ok ? r.json() : null)
            .catch(() => null)
    );

    const postsData = await Promise.all(postPromises);
    return postsData.filter(p => p !== null);
};

module.exports = getMyFavoritesHandler;