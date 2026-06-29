const SearchIndex = require('../models/SearchIndex');

const syncIndexHandler = async (data) => {
    const { postId, title, description, price, categoryId, imageUrl, categoryName, status } = data;
    await SearchIndex.create({ postId, title, description, price, categoryId, imageUrl, categoryName, status });
    return { message: 'Index synced' };
};

module.exports = syncIndexHandler;