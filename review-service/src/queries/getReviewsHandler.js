const { Op } = require('sequelize');
const Review = require('../models/Review');

const getReviewsHandler = async (userId, { rating, hasImage }) => {
    let whereClause = { revieweeId: userId };
    
    if (rating) {
        whereClause.rating = rating;
    }
    
    if (hasImage === 'true') {
        whereClause.imageUrl = { [Op.ne]: null };
    } else if (hasImage === 'false') {
        whereClause.imageUrl = null;
    }

    return await Review.findAll({ 
        where: whereClause,
        order: [['createdAt', 'DESC']]
    });
};

module.exports = getReviewsHandler;