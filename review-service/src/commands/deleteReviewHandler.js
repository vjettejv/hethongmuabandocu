const fs = require('fs');
const path = require('path');
const Review = require('../models/Review');

const deleteReviewHandler = async (id) => {
    const review = await Review.findByPk(id);
    if (!review) throw new Error('Review not found');
    
    if (review.imageUrl) {
        const oldPath = path.join(__dirname, '../../', review.imageUrl);
        if (fs.existsSync(oldPath)) fs.unlinkSync(oldPath);
    }
    
    await review.destroy();
    return { message: 'Review deleted successfully' };
};

module.exports = deleteReviewHandler;