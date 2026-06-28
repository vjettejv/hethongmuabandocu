const createCategoryHandler = require('../commands/createCategoryHandler');

const createCategory = async (req, res) => {
    try {
        const newCategory = await createCategoryHandler(req.body);
        res.status(201).json(newCategory);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};

const createAdminCategory = async (req, res) => {
    try {
        const newCategory = await createCategoryHandler(req.body);
        res.status(201).json({ data: newCategory });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};

module.exports = { createCategory, createAdminCategory };