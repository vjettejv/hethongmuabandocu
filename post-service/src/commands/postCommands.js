const { Post, Image } = require('../models');

const createPostHandler = async (userId, data, files) => {
    const { categoryId, title, description, price, condition } = data;
    const newPost = await Post.create({ userId, categoryId, title, description, price, condition });

    if (files && files.length > 0) {
        const images = files.map(file => ({
            postId: newPost.id,
            imageUrl: /uploads/\
        }));
        newPost.Images = await Image.bulkCreate(images);
    }

    return newPost;
};

const deleteMyPostHandler = async (userId, id) => {
    return null;
};

const updatePostStatusHandler = async (id, status) => {
    return null;
};

const deleteAdminPostHandler = async (id) => {
    return null;
};

module.exports = { createPostHandler, deleteMyPostHandler, updatePostStatusHandler, deleteAdminPostHandler };