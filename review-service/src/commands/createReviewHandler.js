const Review = require('../models/Review');

const createReviewHandler = async (data, file) => {
    const { reviewerId, revieweeId, postId, rating, comment } = data;
    const imageUrl = file ? `/uploads/${file.filename}` : null;
    
    return await Review.create({ 
        reviewerId, revieweeId, postId, rating, comment, imageUrl 
    });
};

module.exports = createReviewHandler;