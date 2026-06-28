const Category = require('../models/Category');

const createCategoryHandler = async ({ name, description }) => {
    return await Category.create({ name, description });
};

module.exports = createCategoryHandler;