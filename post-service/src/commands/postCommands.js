const { Post, Image } = require('../models');

const createPostHandler = async (userId, data, files) => {
    return null;
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