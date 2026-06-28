const getAllCategoriesHandler = require('../queries/getAllCategoriesHandler');

const getAllCategories = async (req, res) => {
    try {
        const categories = await getAllCategoriesHandler();
        res.json(categories);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};

module.exports = { getAllCategories };