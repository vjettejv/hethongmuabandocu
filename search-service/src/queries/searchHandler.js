const { Sequelize } = require('sequelize');
const SearchIndex = require('../models/SearchIndex');

const searchHandler = async ({ query, categoryId, minPrice, maxPrice }) => {
    let whereClause = {};

    if (query) {
        whereClause[Sequelize.Op.or] = [
            { title: { [Sequelize.Op.like]: `%${query}%` } },
            { description: { [Sequelize.Op.like]: `%${query}%` } }
        ];
    }
    
    if (categoryId) whereClause.categoryId = categoryId;
    
    whereClause.status = 'approved';

    if (minPrice || maxPrice) {
        whereClause.price = {};
        if (minPrice) whereClause.price[Sequelize.Op.gte] = minPrice;
        if (maxPrice) whereClause.price[Sequelize.Op.lte] = maxPrice;
    }

    const results = await SearchIndex.findAll({ where: whereClause, order: [['createdAt', 'DESC']] });
    return results.map(r => {
        const data = r.toJSON();
        data.id = data.postId; 
        return data;
    });
};

module.exports = searchHandler;