const Category = require('../models/Category');

const getAllCategoriesHandler = async () => {
    return await Category.findAll();
};

module.exports = getAllCategoriesHandler;