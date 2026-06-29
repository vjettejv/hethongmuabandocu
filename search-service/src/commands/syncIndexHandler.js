const SearchIndex = require('../models/SearchIndex');

const syncIndexHandler = async (data) => {
    return { message: 'Index synced' };
};

module.exports = syncIndexHandler;