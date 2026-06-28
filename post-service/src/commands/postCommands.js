const { Post, Image } = require('../models');

const createPostHandler = async (userId, data, files) => {
    const { categoryId, title, description, price, condition } = data;
    const newPost = await Post.create({ userId, categoryId, title, description, price, condition });
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