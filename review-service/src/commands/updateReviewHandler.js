const fs = require('fs');
const path = require('path');
const Review = require('../models/Review');

const updateReviewHandler = async (id, data, file) => {
    const review = await Review.findByPk(id);
    if (!review) throw new Error('Review not found');
    
    const { rating, comment } = data;
    if (rating) review.rating = rating;
    if (comment) review.comment = comment;
    if (file) {
        if (review.imageUrl) {
            const oldPath = path.join(__dirname, '../../', review.imageUrl);
            if (fs.existsSync(oldPath)) fs.unlinkSync(oldPath);
        }
        review.imageUrl = `/uploads/${file.filename}`;
    }
    
    await review.save();
    return review;
};

module.exports = updateReviewHandler;